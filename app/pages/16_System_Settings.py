import os
import sys
import pandas as pd
import streamlit as st
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.database import get_connection
from src.audit_logger import log_action

st.header("🛠️ System Settings & Role Threshold Configuration")
st.subheader("Configure DB-Backed Planner Authorization Limits & Operational Parameters")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT setting_key, setting_value FROM settings;")
settings_dict = {row[0]: row[1] for row in cursor.fetchall()}

st.markdown("### 🔐 Role Authorization Thresholds (% of Baseline Forecast)")

with st.form("settings_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        jnr_limit = st.number_input("Junior Planner Max Limit (%)", value=float(settings_dict.get("junior_planner_limit_pct", 20.0)), step=5.0)
    with c2:
        snr_limit = st.number_input("Senior Planner Max Limit (%)", value=float(settings_dict.get("senior_planner_limit_pct", 50.0)), step=5.0)
    with c3:
        mgr_limit = st.number_input("Supply Chain Manager Max Limit (%)", value=float(settings_dict.get("manager_limit_pct", 100.0)), step=5.0)

    st.markdown("### 🚛 Driver Safety Limits")
    max_hours = st.number_input("Driver Maximum Safe Weekly Hours", value=float(settings_dict.get("driver_max_safe_hours", 50.0)), step=1.0)

    btn_save = st.form_submit_button("💾 Save System Settings")

if btn_save:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = st.session_state.get("user_id", "U-ADMIN-01")

    updates = [
        ("junior_planner_limit_pct", str(jnr_limit)),
        ("senior_planner_limit_pct", str(snr_limit)),
        ("manager_limit_pct", str(mgr_limit)),
        ("driver_max_safe_hours", str(max_hours))
    ]

    for k, v in updates:
        cursor.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value, updated_at, updated_by) VALUES (?, ?, ?, ?);", (k, v, now_str, user_id))

    conn.commit()
    log_action(conn, user_id, "SETTINGS_UPDATED", "settings", "global", new_value=str(dict(updates)))
    st.success("System settings successfully saved into database!")

st.markdown("---")
st.markdown("### 📋 DB Settings Table Preview")
cursor.execute("SELECT * FROM settings;")
rows = cursor.fetchall()
st.dataframe(pd.DataFrame([dict(r) for r in rows]), use_container_width=True)

conn.close()
