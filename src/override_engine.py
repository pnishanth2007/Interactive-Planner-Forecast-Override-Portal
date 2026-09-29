"""
Override Engine & Authorization Module.
Handles planner demand adjustments, directional percentage changes, DB-backed master reason codes,
and role-based authorization thresholds.
"""

import sqlite3
from datetime import datetime

# Fallback Reason Codes Registry
REASON_CODES = {
    "R01": "Recent equipment failure",
    "R02": "Customer emergency",
    "R03": "Supplier delay",
    "R04": "Historical forecast inaccurate",
    "R05": "Seasonal demand",
    "R06": "Inventory concern",
    "R07": "Planned maintenance",
    "R08": "Data quality issue",
    "R09": "Customer-specific requirement",
    "R10": "Other"
}

# Default Role Limits (% of baseline forecast)
ROLE_AUTHORITY_LIMITS = {
    "Junior Planner": 20.0,
    "Senior Planner": 50.0,
    "Supply Chain Manager": 100.0,
    "Planning Manager": 100.0,
    "Manager": 100.0,
    "Admin": 1000.0,
    "Viewer": 0.0
}

def get_db_reasons(conn=None) -> dict:
    """
    Fetches master reason codes from DB if connected, else returns default dict.
    """
    if conn is None:
        return REASON_CODES
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT reason_code, reason_name FROM override_reasons WHERE is_active = 1;")
        rows = cursor.fetchall()
        if rows:
            return {r[0]: r[1] for r in rows}
    except Exception:
        pass
    return REASON_CODES

def calculate_final_demand(baseline_forecast: int, override_quantity: int) -> int:
    """
    Formula: Final Demand = max(0, Baseline Forecast + Override Quantity)
    Prevents invalid negative demand.
    """
    return max(0, baseline_forecast + override_quantity)

def check_authorization(role: str, baseline_forecast: int, override_quantity: int, conn=None) -> tuple[str, float, float]:
    """
    Verifies if planner has authority to approve the override percentage.
    Returns (status, override_pct, max_allowed_pct).
    """
    max_allowed = ROLE_AUTHORITY_LIMITS.get(role, 20.0)

    # Check DB settings for custom threshold if conn provided
    if conn:
        try:
            cursor = conn.cursor()
            setting_key = f"{role.lower().replace(' ', '_')}_limit_pct"
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key = ?;", (setting_key,))
            row = cursor.fetchone()
            if row:
                max_allowed = float(row[0])
        except Exception:
            pass

    if baseline_forecast == 0:
        pct_change = 100.0 if abs(override_quantity) > 0 else 0.0
    else:
        pct_change = abs(override_quantity / baseline_forecast) * 100.0

    if pct_change <= max_allowed:
        status = "APPROVED"
    else:
        status = "PENDING APPROVAL"

    return status, round(pct_change, 1), max_allowed

def process_planner_override(planner_id: str, role: str, part_id: str, baseline_forecast: int, override_quantity: int, reason_code: str, reason_comment: str = None, conn=None) -> dict:
    """
    Executes full override processing logic: validates reason code, calculates final demand,
    determines direction, and applies authorization rules.
    """
    valid_reasons = get_db_reasons(conn)

    if reason_code not in valid_reasons:
        return {
            "success": False,
            "error": f"Invalid or missing reason code: {reason_code}"
        }

    final_demand = calculate_final_demand(baseline_forecast, override_quantity)
    direction = "INCREASE" if override_quantity >= 0 else "DECREASE"
    abs_change = abs(override_quantity)

    auth_status, pct_change, max_allowed = check_authorization(role, baseline_forecast, override_quantity, conn)

    return {
        "success": True,
        "planner_id": planner_id,
        "role": role,
        "part_id": part_id,
        "baseline_forecast": baseline_forecast,
        "override_quantity": override_quantity,
        "direction": direction,
        "absolute_change": abs_change,
        "final_demand": final_demand,
        "reason_code": reason_code,
        "reason_description": valid_reasons[reason_code],
        "reason_comment": reason_comment or "",
        "override_pct": pct_change,
        "authority_limit_pct": max_allowed,
        "approval_status": auth_status,
        "approval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
