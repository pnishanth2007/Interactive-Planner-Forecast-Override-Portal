"""
Override Learning Engine.
Analyzes historical planner overrides, aggregates success rates by reason, equipment, part, and role,
ranks reason codes, and identifies top performing vs underperforming override patterns.
"""

import pandas as pd
import numpy as np
from src.override_engine import REASON_CODES

def analyze_override_learning(df_eval):
    """
    Core learning algorithm: aggregates performance across dimensions to extract planner override intelligence.
    """
    df_overrides = df_eval[df_eval["Planner_Override"] == "YES"].copy()

    if len(df_overrides) == 0:
        return {}

    # Helper function for grouping and metrics calculation
    def compute_group_metrics(df_sub, group_col):
        grouped = df_sub.groupby(group_col).agg(
            Total_Overrides=("Record_ID", "count"),
            Successful_Overrides=("Override_Improved", lambda x: (x == "YES").sum()),
            Failed_Overrides=("Override_Improved", lambda x: (x == "NO").sum()),
            Avg_Baseline_Error=("Baseline_Error", "mean"),
            Avg_Override_Error=("Override_Error", "mean")
        ).reset_index()

        grouped["Success_Rate_Pct"] = np.round((grouped["Successful_Overrides"] / grouped["Total_Overrides"]) * 100.0, 1)
        grouped["Avg_Improvement_Pct"] = np.round(
            ((grouped["Avg_Baseline_Error"] - grouped["Avg_Override_Error"]) / grouped["Avg_Baseline_Error"]) * 100.0, 1
        ).fillna(0.0)

        grouped["Avg_Baseline_Error"] = np.round(grouped["Avg_Baseline_Error"], 2)
        grouped["Avg_Override_Error"] = np.round(grouped["Avg_Override_Error"], 2)

        return grouped.sort_values(by="Success_Rate_Pct", ascending=False)

    # 1. Learning by Override Reason
    reason_learning = compute_group_metrics(df_overrides, "Override_Reason")
    # Map reason code descriptions
    reason_learning["Reason_Description"] = reason_learning["Override_Reason"].map(REASON_CODES).fillna("Other / Unknown")

    # Reorder columns
    reason_cols = ["Override_Reason", "Reason_Description", "Total_Overrides", "Successful_Overrides", "Failed_Overrides", "Success_Rate_Pct", "Avg_Baseline_Error", "Avg_Override_Error", "Avg_Improvement_Pct"]
    reason_learning = reason_learning[[c for c in reason_cols if c in reason_learning.columns]]

    # 2. Learning by Equipment Type
    equipment_learning = compute_group_metrics(df_overrides, "Equipment_Type")

    # 3. Learning by Part Type
    part_learning = compute_group_metrics(df_overrides, "Part_Name")

    # 4. Learning by Region
    region_learning = compute_group_metrics(df_overrides, "Region")

    # 5. Learning by Demand Pattern
    pattern_learning = compute_group_metrics(df_overrides, "Demand_Pattern")

    # Extract Key Insights & Reason Rankings
    if len(reason_learning) > 0:
        most_successful = reason_learning.iloc[0]
        least_successful = reason_learning.iloc[-1]
        review_required = reason_learning[reason_learning["Success_Rate_Pct"] < 55.0]
    else:
        most_successful = None
        least_successful = None
        review_required = pd.DataFrame()

    return {
        "reason_learning": reason_learning,
        "equipment_learning": equipment_learning,
        "part_learning": part_learning,
        "region_learning": region_learning,
        "pattern_learning": pattern_learning,
        "most_successful_reason": {
            "code": most_successful["Override_Reason"] if most_successful is not None else "N/A",
            "description": most_successful["Reason_Description"] if most_successful is not None else "N/A",
            "success_rate": most_successful["Success_Rate_Pct"] if most_successful is not None else 0.0,
            "improvement": most_successful["Avg_Improvement_Pct"] if most_successful is not None else 0.0
        },
        "least_successful_reason": {
            "code": least_successful["Override_Reason"] if least_successful is not None else "N/A",
            "description": least_successful["Reason_Description"] if least_successful is not None else "N/A",
            "success_rate": least_successful["Success_Rate_Pct"] if least_successful is not None else 0.0,
            "improvement": least_successful["Avg_Improvement_Pct"] if least_successful is not None else 0.0
        },
        "reasons_requiring_review": review_required
    }
