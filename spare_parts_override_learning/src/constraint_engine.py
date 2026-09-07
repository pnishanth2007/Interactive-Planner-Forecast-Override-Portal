"""
Constraint Validation & Multi-Objective Optimization Engine.
Enforces hard rules (supplier capacity, driver safe hours, non-negative demand, reason requirement)
and soft rules (cost, emissions, delivery time targets). Computes trade-off decision scores.
"""

def evaluate_driver_safety(driver_info):
    """
    Evaluates driver workload percentage against safety thresholds:
    <= 80%: SAFE
    80-100%: WARNING
    > 100%: UNSAFE / REJECT
    """
    assigned = float(driver_info.get("assigned_hours", 0))
    max_safe = float(driver_info.get("maximum_safe_hours", 50.0))

    if max_safe <= 0:
        max_safe = 50.0

    workload_pct = round((assigned / max_safe) * 100.0, 1)

    if workload_pct <= 80.0:
        status = "SAFE"
    elif workload_pct <= 100.0:
        status = "WARNING"
    else:
        status = "UNSAFE / REJECT"

    return {
        "driver_id": driver_info.get("driver_id", "D101"),
        "driver_name": driver_info.get("driver_name", "Driver D101"),
        "assigned_hours": assigned,
        "maximum_safe_hours": max_safe,
        "workload_pct": workload_pct,
        "safety_status": status
    }

def validate_hard_constraints(final_demand, supplier_capacity, driver_info=None, override_reason=None):
    """
    Validates mandatory hard constraints.
    Hard constraints must NEVER be violated.
    """
    violations = []
    status = "PASS"

    # 1. Invalid Quantity (demand cannot be negative)
    if final_demand < 0:
        status = "REJECT"
        violations.append(f"Invalid demand quantity: {final_demand}. Demand cannot be negative.")

    # 2. Supplier Capacity
    if final_demand > supplier_capacity:
        status = "REJECT"
        violations.append(f"Final demand ({final_demand}) exceeds supplier capacity ({supplier_capacity}).")

    # 3. Missing Override Reason
    if override_reason is None or str(override_reason).strip() == "":
        status = "REJECT"
        violations.append("Missing override reason. An override reason code (R01-R10) is mandatory.")

    # 4. Driver Maximum Working Hours
    if driver_info:
        driver_eval = evaluate_driver_safety(driver_info)
        if driver_eval["safety_status"] == "UNSAFE / REJECT":
            status = "REJECT"
            violations.append(
                f"Driver Workload Violation: Driver {driver_eval['driver_id']} has {driver_eval['workload_pct']}% workload "
                f"({driver_eval['assigned_hours']}h / {driver_eval['maximum_safe_hours']}h max safe limit)."
            )

    if status == "PASS":
        explanation = "All hard constraints passed successfully."
    else:
        explanation = " | ".join(violations)

    return {
        "status": status,
        "violations": violations,
        "explanation": explanation
    }

def validate_soft_constraints(estimated_cost, cost_target, estimated_emissions, emission_target, delivery_time_hours, preferred_time_hours):
    """
    Evaluates soft constraints. Violations generate warnings but do NOT cause rejection.
    """
    warnings = []
    status = "PASS"

    if estimated_cost > cost_target:
        status = "WARNING"
        warnings.append(f"Cost of ${estimated_cost:,.2f} exceeds target of ${cost_target:,.2f}.")

    if estimated_emissions > emission_target:
        status = "WARNING"
        warnings.append(f"Emissions of {estimated_emissions:.1f} kg exceed target of {emission_target:.1f} kg.")

    if delivery_time_hours > preferred_time_hours:
        status = "WARNING"
        warnings.append(f"Delivery time of {delivery_time_hours:.1f} hrs exceeds preferred {preferred_time_hours:.1f} hrs.")

    if status == "PASS":
        explanation = "All soft targets met."
    else:
        explanation = " | ".join(warnings)

    return {
        "status": status,
        "warnings": warnings,
        "explanation": explanation
    }

def evaluate_multi_objective_score(cost, delivery_time, emissions, reliability_score, strategy="A"):
    """
    Computes normalized decision score (0-100 scale, higher is better) for logistics decisions.
    
    STRATEGY A: Cost-focused
    Cost = 50%, Time = 20%, Emissions = 10%, Reliability = 20%
    
    STRATEGY B: Reliability-focused
    Cost = 15%, Time = 15%, Emissions = 10%, Reliability = 60%
    """
    # Normalize metrics to standard sub-scores (0-100, higher is better)
    # Benchmark assumptions: Cost ~$1000 max, Time ~72h max, Emissions ~250kg max
    cost_subscore = max(0.0, 100.0 - (cost / 1500.0 * 100.0))
    time_subscore = max(0.0, 100.0 - (delivery_time / 96.0 * 100.0))
    emissions_subscore = max(0.0, 100.0 - (emissions / 300.0 * 100.0))
    reliability_subscore = min(100.0, max(0.0, reliability_score))

    if strategy.upper() == "A":
        # Cost-focused
        w_cost, w_time, w_emissions, w_rel = 0.50, 0.20, 0.10, 0.20
        strategy_name = "Strategy A (Cost-Focused)"
    else:
        # Reliability-focused
        w_cost, w_time, w_emissions, w_rel = 0.15, 0.15, 0.10, 0.60
        strategy_name = "Strategy B (Reliability-Focused)"

    total_score = round(
        (cost_subscore * w_cost) +
        (time_subscore * w_time) +
        (emissions_subscore * w_emissions) +
        (reliability_subscore * w_rel),
        2
    )

    return {
        "strategy": strategy_name,
        "total_score": total_score,
        "subscores": {
            "Cost Score": round(cost_subscore, 1),
            "Delivery Time Score": round(time_subscore, 1),
            "Emissions Score": round(emissions_subscore, 1),
            "Reliability Score": round(reliability_subscore, 1)
        },
        "weights": {
            "Cost": f"{int(w_cost*100)}%",
            "Time": f"{int(w_time*100)}%",
            "Emissions": f"{int(w_emissions*100)}%",
            "Reliability": f"{int(w_rel*100)}%"
        }
    }
