"""
Unit tests for Forecast Evaluation, Outcome Measurement, and Target Verification.
"""

import pytest
import pandas as pd
import numpy as np
from src.forecasting import calculate_forecast_metrics
from src.evaluation import evaluate_demand_outcomes, verify_prototype_targets

def test_calculate_forecast_metrics():
    actual = [10, 20, 30, 40, 50]
    forecast = [12, 18, 33, 42, 45]

    metrics = calculate_forecast_metrics(actual, forecast)
    assert "MAE" in metrics
    assert "RMSE" in metrics
    assert "WMAPE" in metrics
    assert "Bias" in metrics
    assert metrics["MAE"] == 2.8  # (|2|+|-2|+|3|+|2|+|-5|)/5 = 14/5 = 2.8

def test_evaluate_demand_outcomes_dataframe():
    df = pd.DataFrame([
        {
            "Record_ID": "REC-000001",
            "Planner_Override": "YES",
            "Baseline_Forecast": 100,
            "Final_Demand": 120,
            "Actual_Demand": 125,
            "Service_Level": 96.0,
            "Stockout_Flag": 0,
            "Emergency_Order_Flag": 0
        },
        {
            "Record_ID": "REC-000002",
            "Planner_Override": "YES",
            "Baseline_Forecast": 50,
            "Final_Demand": 40,
            "Actual_Demand": 20,
            "Service_Level": 100.0,
            "Stockout_Flag": 0,
            "Emergency_Order_Flag": 0
        }
    ])

    df_eval, summary = evaluate_demand_outcomes(df)

    assert "Baseline_Error" in df_eval.columns
    assert "Override_Error" in df_eval.columns
    assert "Override_Improved" in df_eval.columns

    # Record 1: Baseline Error = |100-125|=25, Override Error = |120-125|=5 -> Improved YES
    assert df_eval.iloc[0]["Override_Improved"] == "YES"
    # Record 2: Baseline Error = |50-20|=30, Override Error = |40-20|=20 -> Improved YES
    assert df_eval.iloc[1]["Override_Improved"] == "YES"

def test_verify_prototype_targets():
    sample_summary = {
        "Baseline_MAE": 10.0,
        "Override_MAE": 8.0,
        "MAE_Improvement_Pct": 20.0,
        "Service_Level_Pct": 88.0,
        "Stockout_Rate_Pct": 12.0,
        "Override_Success_Rate_Pct": 75.0
    }

    target_eval = verify_prototype_targets(sample_summary, baseline_service_level_ref=80.0, baseline_stockout_ref=16.0)
    assert target_eval["overall_status"] == "TARGET ACHIEVED"
    assert len(target_eval["targets"]) == 4
