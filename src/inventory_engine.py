"""
Inventory Intelligence & Stock Optimization Engine.
Calculates Reorder Points (ROP), reorder quantity recommendations, expected stockout risks,
and categorizes parts into Critical, Low, Healthy, or Excess stock states.
"""

import numpy as np
import pandas as pd

def calculate_inventory_position(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes inventory intelligence metrics for each part.
    """
    df_inv = df.copy()

    # Reorder Point (ROP) Formula: (Lead_Time_Days * Daily_Demand_Est) + Safety_Stock
    # Daily demand estimated as (Historical_Demand / 30)
    daily_demand = df_inv["Historical_Demand"] / 30.0
    df_inv["Reorder_Point"] = np.round((df_inv["Lead_Time_Days"] * daily_demand) + df_inv["Safety_Stock"]).astype(int)

    # Reorder Quantity Recommendation
    df_inv["Reorder_Recommendation"] = np.maximum(
        0,
        (df_inv["Reorder_Point"] + df_inv["Safety_Stock"]) - df_inv["Inventory_Level"]
    )

    # Inventory Status Classification
    conditions = [
        (df_inv["Inventory_Level"] <= (df_inv["Safety_Stock"] * 0.5)),
        (df_inv["Inventory_Level"] <= df_inv["Reorder_Point"]),
        (df_inv["Inventory_Level"] > (df_inv["Reorder_Point"] * 2.5)),
    ]
    choices = ["Critical Stock", "Low Stock", "Excess Stock"]
    df_inv["Inventory_Status"] = np.select(conditions, choices, default="Healthy Stock")

    return df_inv

def get_inventory_recommendations_summary(df_inv: pd.DataFrame) -> dict:
    """
    Aggregates inventory health metrics for executive dashboards.
    """
    status_counts = df_inv["Inventory_Status"].value_counts().to_dict()
    critical_df = df_inv[df_inv["Inventory_Status"] == "Critical Stock"]
    reorder_df = df_inv[df_inv["Reorder_Recommendation"] > 0]

    return {
        "status_counts": status_counts,
        "critical_parts_count": len(critical_df),
        "reorder_needed_count": len(reorder_df),
        "total_recommended_reorder_units": int(reorder_df["Reorder_Recommendation"].sum()),
        "top_reorder_parts": reorder_df[["Part_ID", "Part_Name", "Inventory_Level", "Safety_Stock", "Reorder_Point", "Reorder_Recommendation", "Inventory_Status"]].drop_duplicates("Part_ID").head(10)
    }
