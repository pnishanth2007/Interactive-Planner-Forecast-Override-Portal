"""
Unit tests for Planner Override Engine and Authorization System.
"""

import pytest
from src.override_engine import (
    calculate_final_demand,
    check_authorization,
    process_planner_override
)

def test_calculate_final_demand():
    assert calculate_final_demand(50, 15) == 65
    assert calculate_final_demand(100, -20) == 80
    assert calculate_final_demand(0, 5) == 5

def test_junior_planner_authorization():
    # 15% change -> <= 20% limit -> APPROVED
    status, pct, max_l = check_authorization("Junior Planner", baseline_forecast=100, override_quantity=15)
    assert status == "APPROVED"
    assert pct == 15.0

    # 25% change -> > 20% limit -> PENDING APPROVAL
    status, pct, max_l = check_authorization("Junior Planner", baseline_forecast=100, override_quantity=25)
    assert status == "PENDING APPROVAL"

def test_senior_planner_authorization():
    # 40% change -> <= 50% limit -> APPROVED
    status, pct, max_l = check_authorization("Senior Planner", baseline_forecast=100, override_quantity=40)
    assert status == "APPROVED"

    # 60% change -> > 50% limit -> PENDING APPROVAL
    status, pct, max_l = check_authorization("Senior Planner", baseline_forecast=100, override_quantity=60)
    assert status == "PENDING APPROVAL"

def test_planning_manager_authorization():
    # 90% change -> <= 100% limit -> APPROVED
    status, pct, max_l = check_authorization("Planning Manager", baseline_forecast=100, override_quantity=90)
    assert status == "APPROVED"

def test_process_planner_override_invalid_reason():
    res = process_planner_override(
        planner_id="U-JUNIOR-01",
        role="Junior Planner",
        part_id="P101",
        baseline_forecast=50,
        override_quantity=5,
        reason_code="INVALID_CODE"
    )
    assert res["success"] is False
    assert "Invalid or missing reason code" in res["error"]
