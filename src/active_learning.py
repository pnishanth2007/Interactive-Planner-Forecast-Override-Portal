"""
Active Learning Feedback Loop & Model Management Engine.
Extracts successful historical planner overrides as learning signals, retrains demand forecasting models,
registers model versions, and manages production model activation.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import HistGradientBoostingRegressor
from src.forecasting import create_time_series_features, calculate_forecast_metrics
from src.audit_logger import log_action

def retrain_model_with_feedback(df: pd.DataFrame, conn: sqlite3.Connection = None, user_id: str = "U-ADMIN-01") -> dict:
    """
    Active Learning pipeline:
    1. Filters historical records where planner overrides improved demand accuracy.
    2. Weights successful override signals into the training dataset.
    3. Retrains HistGradientBoosting model.
    4. Evaluates performance metrics (MAE, RMSE, MAPE, WAPE).
    5. Saves new model version into SQLite `models` table.
    """
    df_eval = df.copy()
    if "Baseline_Error" not in df_eval.columns:
        df_eval["Baseline_Error"] = (df_eval["Baseline_Forecast"] - df_eval["Actual_Demand"]).abs()
        df_eval["Override_Error"] = (df_eval["Final_Demand"] - df_eval["Actual_Demand"]).abs()
        df_eval["Override_Improved"] = np.where(df_eval["Override_Error"] < df_eval["Baseline_Error"], "YES", "NO")

    # Target variable adjustment: for successful overrides, target uses Final_Demand intent as feedback
    successful_mask = (df_eval["Planner_Override"] == "YES") & (df_eval["Override_Improved"] == "YES")
    feedback_df = df_eval.copy()
    feedback_df.loc[successful_mask, "Historical_Demand"] = feedback_df.loc[successful_mask, "Final_Demand"]

    X, y = create_time_series_features(feedback_df)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    model = HistGradientBoostingRegressor(max_iter=100, random_state=42)
    model.fit(X_train, y_train)

    preds = np.round(np.maximum(0, model.predict(X_test))).astype(int)
    metrics = calculate_forecast_metrics(y_test, preds)

    # Generate version string
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    version = f"v{datetime.now().strftime('%Y%m%d.%H%M')}"
    model_name = "Active Learning Gradient Booster"

    new_model_id = None
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO models (model_name, version, training_date, training_rows, mae, rmse, mape, wape, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'INACTIVE');
        """, (model_name, version, now_str, len(feedback_df), metrics["MAE"], metrics["RMSE"], metrics["MAPE"], metrics["WAPE"]))

        new_model_id = cursor.lastrowid
        conn.commit()
        log_action(conn, user_id, "MODEL_TRAINED", "models", str(new_model_id), new_value=f"Version {version} - MAE: {metrics['MAE']}")

    return {
        "success": True,
        "model_id": new_model_id,
        "model_name": model_name,
        "version": version,
        "training_date": now_str,
        "training_rows": len(feedback_df),
        "metrics": metrics,
        "trained_model_object": model
    }

def get_model_history(conn: sqlite3.Connection) -> list:
    """
    Retrieves all trained model versions from SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
    SELECT model_id, model_name, version, training_date, training_rows, mae, rmse, mape, wape, status
    FROM models
    ORDER BY model_id DESC;
    """)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def activate_model_version(conn: sqlite3.Connection, model_id: int, user_id: str = "U-ADMIN-01") -> dict:
    """
    Sets specified model version as ACTIVE and deactivates all others.
    """
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("UPDATE models SET status = 'INACTIVE';")
    cursor.execute("UPDATE models SET status = 'ACTIVE' WHERE model_id = ?;", (model_id,))
    
    # Update settings
    cursor.execute("UPDATE settings SET setting_value = ?, updated_at = ?, updated_by = ? WHERE setting_key = 'active_forecasting_model';", (f"Model_ID_{model_id}", now_str, user_id))
    
    conn.commit()
    log_action(conn, user_id, "MODEL_ACTIVATED", "models", str(model_id), new_value="ACTIVE")

    return {"success": True, "message": f"Model #{model_id} activated as active production model."}
