import os
import sys
import pandas as pd
import streamlit as st
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.preprocessing import clean_data
from src.database import get_connection
from src.override_engine import get_db_reasons, process_planner_override
from src.constraint_engine import validate_hard_constraints

st.header("✍️ Planner Interactive Workbench")
st.subheader("Select Part, Review Baseline & Submit Constrained Demand Overrides")

csv_path = os.path.join(base_dir, "data", "raw", "spare_parts_data.csv")
df_raw = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
df = clean_data(df_raw)

conn = get_connection()
reasons_dict = get_db_reasons(conn)

# Planner Controls
c1, c2, c3 = st.columns(3)
with c1:
    selected_part = st.selectbox("Select Part ID", options=df["Part_ID"].unique())
with c2:
    part_records = df[df["Part_ID"] == selected_part]
    selected_eq = st.selectbox("Select Equipment ID", options=part_records["Equipment_ID"].unique())
with c3:
    planner_role = st.selectbox("Select Your Role", options=["Junior Planner", "Senior Planner", "Supply Chain Manager", "Admin"], index=1)

record_match = part_records[part_records["Equipment_ID"] == selected_eq].iloc[0]

st.markdown("### 📋 Part Parameters & Inventory State")
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Part Name", str(record_match['Part_Name'])[:22])
m2.metric("Baseline Forecast", f"{record_match['Baseline_Forecast']} units")
m3.metric("Historical Demand", f"{record_match['Historical_Demand']} units")
m4.metric("Inventory Level", f"{record_match['Inventory_Level']} units")
m5.metric("Safety Stock", f"{record_match['Safety_Stock']} units")
m6.metric("Supplier Capacity", f"{record_match['Supplier_Capacity']} units")

st.markdown("---")
st.markdown("### ✍️ Enter Demand Override")

with st.form("planner_override_form"):
    f1, f2 = st.columns(2)
    with f1:
        override_qty = st.number_input("Override Quantity (+/- units)", value=15, step=1)
        reason_code = st.selectbox("Mandatory Reason Code", options=list(reasons_dict.keys()), format_func=lambda x: f"{x} — {reasons_dict[x]}")
    with f2:
        reason_comment = st.text_area("Field Rationale / Comment", value=f"Emergency adjustment logged for {record_match['Equipment_Type']}.")
        driver_assigned = st.slider("Assigned Driver Hours", min_value=10.0, max_value=70.0, value=38.0)

    submit_btn = st.form_submit_button("🚀 SUBMIT OVERRIDE")

if submit_btn:
    baseline = int(record_match["Baseline_Forecast"])
    
    auth_res = process_planner_override(
        planner_id=st.session_state.get("user_id", "U-SENIOR-01"),
        role=planner_role,
        part_id=selected_part,
        baseline_forecast=baseline,
        override_quantity=override_qty,
        reason_code=reason_code,
        reason_comment=reason_comment,
        conn=conn
    )

    hard_res = validate_hard_constraints(
        final_demand=auth_res["final_demand"],
        supplier_capacity=int(record_match["Supplier_Capacity"]),
        driver_info={"driver_id": record_match["Driver_ID"], "assigned_hours": driver_assigned, "maximum_safe_hours": 50.0},
        override_reason=reason_code,
        role_auth_status=auth_res["approval_status"]
    )

    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown("**Authorisation Result**")
        st.info(f"{auth_res['approval_status']} ({auth_res['override_pct']}% vs {auth_res['authority_limit_pct']}% max)")

    with r2:
        st.markdown("**Constraint Result**")
        if hard_res["status"] == "PASS":
            st.success("PASS — Constraints satisfied")
        elif hard_res["status"] == "WARNING":
            st.warning(f"WARNING — {hard_res['explanation']}")
        else:
            st.error(f"REJECT — {hard_res['explanation']}")

    with r3:
        st.markdown("**Final Demand**")
        st.metric("Final Demand", f"{auth_res['final_demand']} units", delta=f"{override_qty:+} units")

    # DB Persistence & Approval Record Insertion
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    direction = "INCREASE" if override_qty >= 0 else "DECREASE"

    cursor.execute("""
    INSERT INTO overrides (record_id, planner_id, planner_role, override_quantity, direction, override_pct, reason_code, reason_comment, final_demand, approval_status, approval_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (record_match["Record_ID"], st.session_state.get("user_id", "U-SENIOR-01"), planner_role, override_qty, direction, auth_res["override_pct"], reason_code, reason_comment, auth_res["final_demand"], auth_res["approval_status"], now_str))
    
    override_id = cursor.lastrowid
    cursor.execute("""
    INSERT INTO approvals (override_id, requested_by, status, timestamp)
    VALUES (?, ?, ?, ?);
    """, (override_id, st.session_state.get("user_id", "U-SENIOR-01"), auth_res["approval_status"], now_str))
    conn.commit()
    st.toast("Override recorded in database successfully!", icon="💾")

conn.close()
