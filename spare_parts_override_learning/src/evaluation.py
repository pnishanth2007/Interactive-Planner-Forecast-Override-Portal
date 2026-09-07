"""
Evaluation & Error Analysis Module.
Measures demand outcome accuracy, evaluates baseline vs override error reduction, verifies target achievements,
and performs deep error analysis on worst-performing parts and reasons.
"""

import numpy as np
import pandas as pd
from src.forecasting import calculate_forecast_metrics

def evaluate_demand_outcomes(df):
    """
    Evaluates individual demand records and calculates summary performance metrics
    comparing Baseline Forecast vs Final Demand After Override against Actual Demand.
    """
    df_eval = df.copy()

    # Calculate absolute errors
    df_eval["Baseline_Error"] = (df_eval["Baseline_Forecast"] - df_eval["Actual_Demand"]).abs()
    df_eval["Override_Error"] = (df_eval["Final_Demand"] - df_eval["Actual_Demand"]).abs()

    # Determine if override improved demand accuracy
    df_eval["Override_Improved"] = np.where(df_eval["Override_Error"] < df_eval["Baseline_Error"], "YES", "NO")

    # Aggregate metric calculations
    base_metrics = calculate_forecast_metrics(df_eval["Actual_Demand"], df_eval["Baseline_Forecast"])
    override_metrics = calculate_forecast_metrics(df_eval["Actual_Demand"], df_eval["Final_Demand"])

    total_records = len(df_eval)
    total_overrides = len(df_eval[df_eval["Planner_Override"] == "YES"])
    successful_overrides = len(df_eval[(df_eval["Planner_Override"] == "YES") & (df_eval["Override_Improved"] == "YES")])
    
    success_rate = round((successful_overrides / total_overrides * 100.0), 2) if total_overrides > 0 else 0.0

    service_level = round(df_eval["Service_Level"].mean(), 2)
    stockout_rate = round((df_eval["Stockout_Flag"].sum() / total_records * 100.0), 2)
    emergency_order_rate = round((df_eval["Emergency_Order_Flag"].sum() / total_records * 100.0), 2)

    summary = {
        "Total_Records": total_records,
        "Total_Overrides": total_overrides,
        "Successful_Overrides": successful_overrides,
        "Override_Success_Rate_Pct": success_rate,
        "Baseline_MAE": base_metrics["MAE"],
        "Override_MAE": override_metrics["MAE"],
        "MAE_Improvement_Pct": round(((base_metrics["MAE"] - override_metrics["MAE"]) / base_metrics["MAE"] * 100.0), 2) if base_metrics["MAE"] > 0 else 0.0,
        "Baseline_WMAPE": base_metrics["WMAPE"],
        "Override_WMAPE": override_metrics["WMAPE"],
        "Baseline_Bias": base_metrics["Bias"],
        "Override_Bias": override_metrics["Bias"],
        "Service_Level_Pct": service_level,
        "Stockout_Rate_Pct": stockout_rate,
        "Emergency_Order_Rate_Pct": emergency_order_rate
    }

    return df_eval, summary

def verify_prototype_targets(summary_metrics, baseline_service_level_ref=82.0, baseline_stockout_ref=18.0):
    """
    Verifies prototype performance against pre-defined target criteria:
    1. MAE Improvement >= 10%
    2. Service Level Increase >= +5 percentage points
    3. Override Success Rate > 65%
    4. Stockout Rate Reduction >= 10%
    """
    mae_imp = summary_metrics["MAE_Improvement_Pct"]
    success_rate = summary_metrics["Override_Success_Rate_Pct"]
    current_sl = summary_metrics["Service_Level_Pct"]
    current_stockout = summary_metrics["Stockout_Rate_Pct"]

    sl_increase = current_sl - baseline_service_level_ref
    stockout_reduction = ((baseline_stockout_ref - current_stockout) / baseline_stockout_ref * 100.0) if baseline_stockout_ref > 0 else 0.0

    targets = [
        {
            "Metric": "MAE Reduction",
            "Baseline": f"{summary_metrics['Baseline_MAE']:.2f}",
            "Achieved": f"{summary_metrics['Override_MAE']:.2f} ({mae_imp:+.1f}%)",
            "Target": "Improve MAE by ≥ 10%",
            "Passed": mae_imp >= 10.0
        },
        {
            "Metric": "Service Level",
            "Baseline": f"{baseline_service_level_ref:.1f}%",
            "Achieved": f"{current_sl:.1f}% ({sl_increase:+.1f}% pts)",
            "Target": "Increase Service Level by ≥ +5 pts",
            "Passed": sl_increase >= 5.0
        },
        {
            "Metric": "Override Success Rate",
            "Baseline": "N/A",
            "Achieved": f"{success_rate:.1f}%",
            "Target": "Override Success Rate > 65%",
            "Passed": success_rate > 65.0
        },
        {
            "Metric": "Stockout Rate Reduction",
            "Baseline": f"{baseline_stockout_ref:.1f}%",
            "Achieved": f"{current_stockout:.1f}% ({stockout_reduction:+.1f}%)",
            "Target": "Reduce Stockouts by ≥ 10%",
            "Passed": stockout_reduction >= 10.0
        }
    ]

    all_passed = all(t["Passed"] for t in targets)
    overall_status = "TARGET ACHIEVED" if all_passed else "TARGET PARTIALLY ACHIEVED"

    return {
        "overall_status": overall_status,
        "targets": targets
    }

def analyze_error_patterns(df_eval):
    """
    Identifies top error drivers: worst-performing parts, equipment types, override reasons, and spikes.
    """
    # 1. Worst Performing Parts (Highest Mean Override Error)
    worst_parts = df_eval.groupby("Part_Name").agg(
        Records=("Record_ID", "count"),
        Avg_Baseline_Error=("Baseline_Error", "mean"),
        Avg_Override_Error=("Override_Error", "mean")
    ).reset_index().sort_values(by="Avg_Override_Error", ascending=False).head(5)

    # 2. Worst Performing Equipment Types
    worst_eq = df_eval.groupby("Equipment_Type").agg(
        Records=("Record_ID", "count"),
        Avg_Baseline_Error=("Baseline_Error", "mean"),
        Avg_Override_Error=("Override_Error", "mean")
    ).reset_index().sort_values(by="Avg_Override_Error", ascending=False).head(5)

    # 3. Demand Spikes (Actual Demand > 3x Historical Demand)
    spikes = df_eval[df_eval["Actual_Demand"] > (df_eval["Historical_Demand"] * 3)]

    # 4. Stockout Events
    stockouts = df_eval[df_eval["Stockout_Flag"] == 1]

    return {
        "worst_parts": worst_parts,
        "worst_equipment": worst_eq,
        "spike_events_count": len(spikes),
        "stockout_events_count": len(stockouts)
    }
