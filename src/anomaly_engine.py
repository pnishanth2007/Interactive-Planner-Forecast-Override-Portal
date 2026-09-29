"""
Irregular Failure Pattern & Anomaly Engine.
Detects sudden demand spikes, intermittent failures, equipment clusters, and supplier disruptions.
Computes anomaly scores and risk levels (Normal, Elevated, High Risk, Critical).
"""

import numpy as np
import pandas as pd

def detect_irregular_failure_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies irregular failure events and assigns anomaly risk levels.
    """
    df_anomaly = df.copy()

    hist = df_anomaly["Historical_Demand"]
    actual = df_anomaly["Actual_Demand"]

    # Calculate deviation ratio and absolute difference
    df_anomaly["Deviation_Qty"] = actual - hist
    df_anomaly["Deviation_Pct"] = np.round(
        np.where(hist > 0, ((actual - hist) / hist) * 100.0, np.where(actual > 0, 100.0, 0.0)),
        1
    )

    # Statistical Z-score calculation on actual demand
    std_val = actual.std()
    mean_val = actual.mean()
    if std_val > 0:
        df_anomaly["Z_Score"] = np.round((actual - mean_val) / std_val, 2)
    else:
        df_anomaly["Z_Score"] = 0.0

    # Risk Level Categorization Logic
    conditions = [
        (df_anomaly["Demand_Pattern"] == "Sudden spike") | (actual > (hist * 3.5)),
        (df_anomaly["Demand_Pattern"] == "Emergency demand") | (df_anomaly["Z_Score"] > 2.5),
        (df_anomaly["Demand_Pattern"] == "Equipment failure cluster") | (df_anomaly["Z_Score"] > 1.5),
        (df_anomaly["Demand_Pattern"] == "Intermittent demand") | (df_anomaly["Deviation_Pct"].abs() > 50.0)
    ]

    choices = ["Critical", "High Risk", "Elevated", "Elevated"]
    df_anomaly["Risk_Level"] = np.select(conditions, choices, default="Normal")

    return df_anomaly

def get_failure_risk_summary(df_anomaly: pd.DataFrame) -> dict:
    """
    Generates summary metrics of detected failure risks across parts and equipment.
    """
    critical_df = df_anomaly[df_anomaly["Risk_Level"] == "Critical"]
    high_df = df_anomaly[df_anomaly["Risk_Level"] == "High Risk"]

    top_critical_parts = critical_df.groupby("Part_Name").size().reset_index(name="Spike_Events").sort_values("Spike_Events", ascending=False).head(5)
    top_critical_equipment = critical_df.groupby("Equipment_Type").size().reset_index(name="Cluster_Events").sort_values("Cluster_Events", ascending=False).head(5)

    return {
        "total_anomalies": len(critical_df) + len(high_df),
        "critical_count": len(critical_df),
        "high_risk_count": len(high_df),
        "top_critical_parts": top_critical_parts,
        "top_critical_equipment": top_critical_equipment
    }
