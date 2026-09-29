import os
import sys
import pandas as pd
import streamlit as st

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.database import get_connection
from app.components.export_button import render_export_widgets

st.header("📑 Override History & Audit Management")
st.subheader("Filter, Search, and Audit Submitted Planner Overrides")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
SELECT o.override_id, o.record_id, o.planner_id, o.planner_role, o.override_quantity,
       o.direction, o.override_pct, o.reason_code, o.reason_comment, o.final_demand,
       o.approval_status, o.approval_time,
       f.part_id, f.baseline_forecast, f.actual_demand
FROM overrides o
LEFT JOIN forecasts f ON o.record_id = f.record_id
ORDER BY o.override_id DESC
LIMIT 500;
""")

rows = cursor.fetchall()
conn.close()

if rows:
    df_overrides = pd.DataFrame([dict(r) for r in rows])

    st.markdown("### 🔍 Filter Overrides")
    c1, c2, c3 = st.columns(3)
    with c1:
        status_filter = st.multiselect("Filter Approval Status", options=df_overrides["approval_status"].unique(), default=df_overrides["approval_status"].unique())
    with c2:
        reason_filter = st.multiselect("Filter Reason Code", options=df_overrides["reason_code"].dropna().unique())
    with c3:
        role_filter = st.multiselect("Filter Planner Role", options=df_overrides["planner_role"].unique(), default=df_overrides["planner_role"].unique())

    filtered_df = df_overrides[
        df_overrides["approval_status"].isin(status_filter) &
        df_overrides["planner_role"].isin(role_filter)
    ]
    if reason_filter:
        filtered_df = filtered_df[filtered_df["reason_code"].isin(reason_filter)]

    st.dataframe(filtered_df, use_container_width=True)

    st.markdown("---")
    render_export_widgets(filtered_df, "planner_overrides_report")
else:
    st.info("No overrides recorded in database yet.")
