"""
Override Engine & Authorization Module.
Handles planner demand adjustments, reason code mapping, final demand calculation, and role-based approval thresholds.
"""

from datetime import datetime

# Reason Codes Registry
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

# Role Limits (% of baseline forecast)
ROLE_AUTHORITY_LIMITS = {
    "Junior Planner": 20.0,
    "Senior Planner": 50.0,
    "Planning Manager": 100.0
}

def calculate_final_demand(baseline_forecast, override_quantity):
    """
    Formula: Final Demand = Baseline Forecast + Override Quantity
    """
    return baseline_forecast + override_quantity

def check_authorization(role, baseline_forecast, override_quantity):
    """
    Verifies if planner has authority to approve the override percentage.
    Returns (status, pct_change, max_allowed_pct).
    """
    if role not in ROLE_AUTHORITY_LIMITS:
        return "REJECTED", 0.0, 0.0

    max_allowed = ROLE_AUTHORITY_LIMITS[role]

    if baseline_forecast == 0:
        pct_change = 100.0 if abs(override_quantity) > 0 else 0.0
    else:
        pct_change = abs(override_quantity / baseline_forecast) * 100.0

    if pct_change <= max_allowed:
        status = "APPROVED"
    else:
        status = "PENDING APPROVAL"

    return status, round(pct_change, 1), max_allowed

def process_planner_override(planner_id, role, part_id, baseline_forecast, override_quantity, reason_code, reason_comment=None):
    """
    Executes full override processing logic: validates reason code, calculates final demand,
    and applies authorization rules.
    """
    if reason_code not in REASON_CODES:
        return {
            "success": False,
            "error": f"Invalid or missing reason code: {reason_code}"
        }

    final_demand = calculate_final_demand(baseline_forecast, override_quantity)
    auth_status, pct_change, max_allowed = check_authorization(role, baseline_forecast, override_quantity)

    return {
        "success": True,
        "planner_id": planner_id,
        "role": role,
        "part_id": part_id,
        "baseline_forecast": baseline_forecast,
        "override_quantity": override_quantity,
        "final_demand": final_demand,
        "reason_code": reason_code,
        "reason_description": REASON_CODES[reason_code],
        "reason_comment": reason_comment or "",
        "override_pct": pct_change,
        "authority_limit_pct": max_allowed,
        "approval_status": auth_status,
        "approval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
