import os
import sys
import pandas as pd
import streamlit as st

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.constraint_engine import validate_hard_constraints, evaluate_driver_safety

st.header("🛡️ Operational Constraint & Safety Monitor")
st.subheader("Hard Constraints, Soft Optimization Targets & Driver Workload Inspection")

st.markdown("### 🧪 Operational Failure Cases Demonstration")
st.info("Interactive failure scenarios demonstrating automated system rejection rules:")

case_choice = st.radio(
    "Select Failure Scenario:",
    [
        "CASE 1: Override Exceeds Supplier Capacity (Expected: REJECT)",
        "CASE 2: Driver Workload Exceeds Safe Limit (Expected: REJECT)",
        "CASE 3: Override Submitted Without Reason (Expected: REJECT)",
        "CASE 4: Negative Final Demand Entered (Expected: REJECT)",
        "CASE 5: Large Override Exceeding Role Limits (Expected: WARNING / PENDING APPROVAL)"
    ]
)

if "CASE 1" in case_choice:
    res = validate_hard_constraints(final_demand=160, supplier_capacity=100, override_reason="R01")
    st.error(f"STATUS: REJECT | Reason: {res['explanation']}")
elif "CASE 2" in case_choice:
    res = validate_hard_constraints(final_demand=40, supplier_capacity=100, driver_info={"driver_id": "D104", "assigned_hours": 58.0, "maximum_safe_hours": 50.0}, override_reason="R02")
    st.error(f"STATUS: REJECT | Reason: {res['explanation']}")
elif "CASE 3" in case_choice:
    res = validate_hard_constraints(final_demand=30, supplier_capacity=100, override_reason="")
    st.error(f"STATUS: REJECT | Reason: {res['explanation']}")
elif "CASE 4" in case_choice:
    res = validate_hard_constraints(final_demand=-15, supplier_capacity=100, override_reason="R04")
    st.error(f"STATUS: REJECT | Reason: {res['explanation']}")
elif "CASE 5" in case_choice:
    res = validate_hard_constraints(final_demand=80, supplier_capacity=100, override_reason="R01", role_auth_status="PENDING APPROVAL")
    st.warning(f"STATUS: WARNING | Reason: {res['explanation']}")

st.markdown("---")
st.markdown("### 🚛 Driver Workload Safety Roster")
drivers = [
    {"Driver_ID": "D101", "Name": "Driver D101", "Assigned_Hours": 32.0, "Max_Safe": 50.0, "Workload_%": 64.0, "Safety_Status": "SAFE"},
    {"Driver_ID": "D102", "Name": "Driver D102", "Assigned_Hours": 44.0, "Max_Safe": 50.0, "Workload_%": 88.0, "Safety_Status": "WARNING"},
    {"Driver_ID": "D103", "Name": "Driver D103", "Assigned_Hours": 56.0, "Max_Safe": 50.0, "Workload_%": 112.0, "Safety_Status": "UNSAFE / REJECT"}
]
st.dataframe(pd.DataFrame(drivers), use_container_width=True)
