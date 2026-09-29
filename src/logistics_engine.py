"""
Driver Safety & Logistics Simulation Engine.
Calculates driver workload, fatigue risk scoring, traffic congestion impacts, and route feasibility.
"""

import numpy as np
import pandas as pd

def evaluate_driver_logistics_safety(driver_info: dict, delivery_dist_km: float = 100.0, traffic_level: str = "Moderate") -> dict:
    """
    Evaluates driver workload safety, fatigue risk, and route feasibility.
    """
    assigned = float(driver_info.get("assigned_hours", 30.0))
    max_safe = float(driver_info.get("maximum_safe_hours", 50.0))
    if max_safe <= 0:
        max_safe = 50.0

    workload_pct = round((assigned / max_safe) * 100.0, 1)

    # Traffic delay multiplier
    traffic_multipliers = {
        "Low": 1.0,
        "Moderate": 1.2,
        "Heavy": 1.5,
        "Severe Congestion": 2.0
    }
    traffic_mult = traffic_multipliers.get(traffic_level, 1.2)
    est_drive_hours = round((delivery_dist_km / 60.0) * traffic_mult, 1)

    projected_hours = round(assigned + est_drive_hours, 1)
    fatigue_risk_score = round(min(100.0, (projected_hours / max_safe) * 100.0), 1)

    if fatigue_risk_score <= 80.0:
        safety_status = "SAFE"
    elif fatigue_risk_score <= 100.0:
        safety_status = "WARNING"
    elif fatigue_risk_score <= 115.0:
        safety_status = "HIGH RISK"
    else:
        safety_status = "BLOCKED"

    return {
        "driver_id": driver_info.get("driver_id", "D101"),
        "driver_name": driver_info.get("driver_name", "Driver D101"),
        "assigned_hours": assigned,
        "maximum_safe_hours": max_safe,
        "delivery_dist_km": delivery_dist_km,
        "est_drive_hours": est_drive_hours,
        "projected_hours": projected_hours,
        "fatigue_risk_score": fatigue_risk_score,
        "traffic_level": traffic_level,
        "safety_status": safety_status,
        "is_dispatch_allowed": safety_status in ["SAFE", "WARNING"]
    }
