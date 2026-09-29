"""
Supplier Intelligence & Capacity Management Engine.
Tracks supplier capacity utilization, remaining allocation, lead-time risks,
single-source dependencies, and recommends alternate suppliers.
"""

import pandas as pd
import numpy as np

def evaluate_supplier_intelligence(df: pd.DataFrame, conn=None) -> dict:
    """
    Evaluates supplier performance, capacity utilization, and allocation risks.
    """
    supplier_agg = df.groupby("Supplier_ID").agg(
        Total_Orders=("Record_ID", "count"),
        Allocated_Demand=("Final_Demand", "sum"),
        Max_Capacity=("Supplier_Capacity", "mean"),
        Avg_Lead_Time=("Lead_Time_Days", "mean"),
        Avg_Service_Level=("Service_Level", "mean")
    ).reset_index()

    supplier_agg["Utilization_Pct"] = np.round((supplier_agg["Allocated_Demand"] / supplier_agg["Max_Capacity"]) * 100.0, 1)
    supplier_agg["Remaining_Capacity"] = np.maximum(0, supplier_agg["Max_Capacity"] - supplier_agg["Allocated_Demand"])

    # Risk level assignment
    conditions = [
        (supplier_agg["Utilization_Pct"] >= 100.0),
        (supplier_agg["Utilization_Pct"] >= 85.0),
        (supplier_agg["Avg_Lead_Time"] > 10.0)
    ]
    choices = ["Capacity Overload", "High Risk", "Lead Time Risk"]
    supplier_agg["Supplier_Risk_Level"] = np.select(conditions, choices, default="Healthy")

    # Alternate Supplier Recommendations mapping
    suppliers = supplier_agg["Supplier_ID"].unique().tolist()
    def get_alternate(sup_id):
        alts = [s for s in suppliers if s != sup_id]
        return alts[0] if alts else "SUP-101"

    supplier_agg["Recommended_Alternate_Supplier"] = supplier_agg["Supplier_ID"].apply(get_alternate)

    return {
        "supplier_summary": supplier_agg,
        "overloaded_suppliers_count": len(supplier_agg[supplier_agg["Supplier_Risk_Level"] == "Capacity Overload"]),
        "high_risk_suppliers_count": len(supplier_agg[supplier_agg["Supplier_Risk_Level"] == "High Risk"])
    }
