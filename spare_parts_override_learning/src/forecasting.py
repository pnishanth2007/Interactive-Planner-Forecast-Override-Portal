"""
Forecasting Module.
Implements Moving Average (default) and Random Forest forecasting models along with standard accuracy metrics.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from src.preprocessing import prepare_forecasting_features

def moving_average_forecast(historical_series, window=3):
    """
    Computes a simple Moving Average forecast based on historical demand.
    """
    if len(historical_series) == 0:
        return 0
    if len(historical_series) < window:
        return int(round(np.mean(historical_series)))
    return int(round(np.mean(historical_series[-window:])))

def random_forest_forecast(df, test_size=0.2, n_estimators=50, random_state=42):
    """
    Fits a Random Forest Regressor to predict spare parts demand.
    """
    X, y = prepare_forecasting_features(df)
    
    split_idx = int(len(X) * (1 - test_size))
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    rf = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
    rf.fit(X_train, y_train)

    predictions = np.round(rf.predict(X_test)).astype(int)
    predictions = np.maximum(0, predictions)

    return y_test.values, predictions, rf

def calculate_forecast_metrics(actual, forecast):
    """
    Calculates forecast evaluation metrics: MAE, RMSE, MAPE, WMAPE, and Bias.
    """
    actual = np.array(actual, dtype=float)
    forecast = np.array(forecast, dtype=float)

    errors = forecast - actual
    abs_errors = np.abs(errors)

    mae = np.mean(abs_errors)
    rmse = np.sqrt(np.mean(errors ** 2))

    # MAPE: avoid division by zero
    non_zero_mask = actual > 0
    if np.sum(non_zero_mask) > 0:
        mape = np.mean(abs_errors[non_zero_mask] / actual[non_zero_mask]) * 100.0
    else:
        mape = 0.0

    # WMAPE: Weighted Mean Absolute Percentage Error
    total_actual = np.sum(actual)
    if total_actual > 0:
        wmape = (np.sum(abs_errors) / total_actual) * 100.0
    else:
        wmape = 0.0

    # Bias (Mean Error: forecast - actual)
    bias = np.mean(errors)

    return {
        "MAE": round(float(mae), 2),
        "RMSE": round(float(rmse), 2),
        "MAPE": round(float(mape), 2),
        "WMAPE": round(float(wmape), 2),
        "Bias": round(float(bias), 2)
    }
