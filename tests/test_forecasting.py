"""
Unit tests for Advanced Demand Forecasting and Model Comparison.
"""

import pytest
import pandas as pd
import numpy as np
from src.forecasting import create_time_series_features, evaluate_all_models, calculate_forecast_metrics

def test_time_series_features_generation():
    df = pd.DataFrame([
        {
            "Failure_Date": f"2025-01-{i:02d}",
            "Historical_Demand": 10 + i,
            "Actual_Demand": 12 + i,
            "Part_ID": "P101",
            "Equipment_Type": "Turbine",
            "Region": "North America",
            "Failure_Type": "Wear",
            "Inventory_Level": 50,
            "Safety_Stock": 10,
            "Supplier_Capacity": 100,
            "Lead_Time_Days": 5
        } for i in range(1, 25)
    ])

    X, y = create_time_series_features(df)
    assert len(X) == 24
    assert "lag_1" in X.columns
    assert "rolling_mean_7" in X.columns

def test_evaluate_all_models_runs():
    df = pd.DataFrame([
        {
            "Failure_Date": f"2025-01-{(i%28)+1:02d}",
            "Historical_Demand": 20 + (i % 5),
            "Actual_Demand": 22 + (i % 7),
            "Part_ID": f"P10{(i%3)+1}",
            "Equipment_Type": "Excavator",
            "Region": "Europe",
            "Failure_Type": "Thermal",
            "Inventory_Level": 40,
            "Safety_Stock": 10,
            "Supplier_Capacity": 120,
            "Lead_Time_Days": 4
        } for i in range(1, 40)
    ])

    res_df = evaluate_all_models(df)
    assert len(res_df) >= 4
    assert "Model" in res_df.columns
    assert "WAPE" in res_df.columns
