"""
Unit tests for Constraint Engine (Hard constraints, soft constraints, driver safety).
"""

import pytest
from src.constraint_engine import (
    validate_hard_constraints,
    validate_soft_constraints,
    evaluate_driver_safety
)

def test_hard_constraints_pass():
    res = validate_hard_constraints(
        final_demand=50,
        supplier_capacity=100,
        driver_info={"driver_id": "D101", "assigned_hours": 30.0, "maximum_safe_hours": 50.0},
        override_reason="R01"
    )
    assert res["status"] == "PASS"
    assert len(res["violations"]) == 0

def test_supplier_capacity_violation():
    res = validate_hard_constraints(
        final_demand=120,
        supplier_capacity=100,
        driver_info={"driver_id": "D101", "assigned_hours": 30.0, "maximum_safe_hours": 50.0},
        override_reason="R01"
    )
    assert res["status"] == "REJECT"
    assert any("exceeds supplier capacity" in v for v in res["violations"])

def test_negative_demand_violation():
    res = validate_hard_constraints(
        final_demand=-5,
        supplier_capacity=100,
        driver_info={"driver_id": "D101", "assigned_hours": 30.0, "maximum_safe_hours": 50.0},
        override_reason="R01"
    )
    assert res["status"] == "REJECT"
    assert any("Demand cannot be negative" in v for v in res["violations"])

def test_missing_reason_violation():
    res = validate_hard_constraints(
        final_demand=30,
        supplier_capacity=100,
        driver_info={"driver_id": "D101", "assigned_hours": 30.0, "maximum_safe_hours": 50.0},
        override_reason=None
    )
    assert res["status"] == "REJECT"
    assert any("Missing override reason" in v for v in res["violations"])

def test_driver_workload_safety_levels():
    # Safe <= 80%
    safe_eval = evaluate_driver_safety({"driver_id": "D101", "assigned_hours": 35.0, "maximum_safe_hours": 50.0})
    assert safe_eval["safety_status"] == "SAFE"

    # Warning 80-100%
    warn_eval = evaluate_driver_safety({"driver_id": "D102", "assigned_hours": 45.0, "maximum_safe_hours": 50.0})
    assert warn_eval["safety_status"] == "WARNING"

    # Unsafe > 100%
    unsafe_eval = evaluate_driver_safety({"driver_id": "D103", "assigned_hours": 55.0, "maximum_safe_hours": 50.0})
    assert unsafe_eval["safety_status"] == "UNSAFE / REJECT"

def test_driver_workload_hard_rejection():
    res = validate_hard_constraints(
        final_demand=30,
        supplier_capacity=100,
        driver_info={"driver_id": "D104", "assigned_hours": 55.0, "maximum_safe_hours": 50.0},
        override_reason="R02"
    )
    assert res["status"] == "REJECT"
    assert any("Driver Workload Violation" in v for v in res["violations"])
