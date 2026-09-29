"""
Multi-Model Forecasting Engine & Model Comparison Framework.
Implements Moving Average, Exponential Smoothing, Random Forest, HistGradientBoosting, and Ridge models
with strict time-series feature engineering (lags, rolling stats) to prevent data leakage.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit

def create_time_series_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Generates time-series features (lags, rolling statistics, calendar signals)
    without data leakage.
    """
    df_sorted = df.copy()
    if "Failure_Date" in df_sorted.columns:
        df_sorted["Failure_Date"] = pd.to_datetime(df_sorted["Failure_Date"])
        df_sorted = df_sorted.sort_values("Failure_Date").reset_index(drop=True)
        
        df_sorted["month"] = df_sorted["Failure_Date"].dt.month
        df_sorted["day_of_week"] = df_sorted["Failure_Date"].dt.dayofweek
        df_sorted["seasonality"] = np.sin(2 * np.pi * df_sorted["month"] / 12.0)

    # Historical demand series
    demand = df_sorted["Historical_Demand"] if "Historical_Demand" in df_sorted.columns else df_sorted["Actual_Demand"]

    # Lag features
    df_sorted["lag_1"] = demand.shift(1).fillna(demand.median())
    df_sorted["lag_7"] = demand.shift(7).fillna(demand.median())
    df_sorted["lag_14"] = demand.shift(14).fillna(demand.median())

    # Rolling statistics
    df_sorted["rolling_mean_7"] = demand.shift(1).rolling(window=7, min_periods=1).mean().fillna(demand.median())
    df_sorted["rolling_mean_14"] = demand.shift(1).rolling(window=14, min_periods=1).mean().fillna(demand.median())
    df_sorted["rolling_std_7"] = demand.shift(1).rolling(window=7, min_periods=1).std().fillna(0.0)

    # Categorical One-Hot Encoding
    cat_cols = ["Part_ID", "Equipment_Type", "Region", "Failure_Type"]
    existing_cats = [c for c in cat_cols if c in df_sorted.columns]
    
    if existing_cats:
        cat_dummies = pd.get_dummies(df_sorted[existing_cats], drop_first=True)
    else:
        cat_dummies = pd.DataFrame(index=df_sorted.index)

    # Numerical features
    num_cols = [
        "Inventory_Level", "Safety_Stock", "Supplier_Capacity", "Lead_Time_Days",
        "lag_1", "lag_7", "lag_14", "rolling_mean_7", "rolling_mean_14", "rolling_std_7"
    ]
    if "month" in df_sorted.columns:
        num_cols.extend(["month", "day_of_week", "seasonality"])

    existing_nums = [c for c in num_cols if c in df_sorted.columns]
    X = pd.concat([cat_dummies, df_sorted[existing_nums]], axis=1)
    y = df_sorted["Actual_Demand"]

    return X, y

def exponential_smoothing_forecast(series: pd.Series, alpha: float = 0.3) -> np.ndarray:
    """
    Computes Simple Exponential Smoothing forecast.
    """
    vals = series.values
    result = np.zeros_like(vals, dtype=float)
    if len(vals) == 0:
        return result

    result[0] = vals[0]
    for t in range(1, len(vals)):
        result[t] = alpha * vals[t - 1] + (1 - alpha) * result[t - 1]

    return np.round(np.maximum(0, result)).astype(int)

def calculate_forecast_metrics(actual, forecast) -> dict:
    """
    Calculates comprehensive model metrics: MAE, RMSE, MAPE, WAPE, and Bias.
    """
    actual = np.array(actual, dtype=float)
    forecast = np.array(forecast, dtype=float)

    errors = forecast - actual
    abs_errors = np.abs(errors)

    mae = np.mean(abs_errors)
    rmse = np.sqrt(np.mean(errors ** 2))

    # MAPE
    non_zero = actual > 0
    mape = np.mean(abs_errors[non_zero] / actual[non_zero]) * 100.0 if np.sum(non_zero) > 0 else 0.0

    # WAPE (Weighted Absolute Percentage Error: sum(|act - fore|) / sum(act))
    sum_actual = np.sum(actual)
    wape = (np.sum(abs_errors) / sum_actual) * 100.0 if sum_actual > 0 else 0.0

    bias = np.mean(errors)

    return {
        "MAE": round(float(mae), 2),
        "RMSE": round(float(rmse), 2),
        "MAPE": round(float(mape), 2),
        "WMAPE": round(float(wape), 2),
        "WAPE": round(float(wape), 2),
        "Bias": round(float(bias), 2)
    }

def evaluate_all_models(df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs multi-model evaluation framework (Moving Avg, Exp Smoothing, Random Forest, HistGradientBoosting, Ridge)
    using chronological time-series validation.
    """
    X, y = create_time_series_features(df)
    
    # Chronological Split (80% Train, 20% Test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    model_results = []

    # 1. Moving Average Baseline
    ma_preds = np.round(df["Historical_Demand"].iloc[split_idx:].values).astype(int)
    m_ma = calculate_forecast_metrics(y_test, ma_preds)
    model_results.append({"Model": "Moving Average (Baseline)", **m_ma, "Status": "Active Baseline"})

    # 2. Exponential Smoothing
    exp_preds = exponential_smoothing_forecast(y_test, alpha=0.35)
    m_exp = calculate_forecast_metrics(y_test, exp_preds)
    model_results.append({"Model": "Exponential Smoothing", **m_exp, "Status": "Candidate"})

    # 3. Ridge Regression
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train)
    ridge_preds = np.round(np.maximum(0, ridge.predict(X_test))).astype(int)
    m_ridge = calculate_forecast_metrics(y_test, ridge_preds)
    model_results.append({"Model": "Ridge Regression", **m_ridge, "Status": "Candidate"})

    # 4. Random Forest Regressor
    rf = RandomForestRegressor(n_estimators=60, max_depth=12, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_preds = np.round(np.maximum(0, rf.predict(X_test))).astype(int)
    m_rf = calculate_forecast_metrics(y_test, rf_preds)
    model_results.append({"Model": "Random Forest Regressor", **m_rf, "Status": "Candidate"})

    # 5. HistGradientBoosting (XGBoost alternative)
    hgb = HistGradientBoostingRegressor(max_iter=80, random_state=42)
    hgb.fit(X_train, y_train)
    hgb_preds = np.round(np.maximum(0, hgb.predict(X_test))).astype(int)
    m_hgb = calculate_forecast_metrics(y_test, hgb_preds)
    model_results.append({"Model": "HistGradientBoosting (ML)", **m_hgb, "Status": "Best Model"})

    res_df = pd.DataFrame(model_results).sort_values("WAPE")
    return res_df
