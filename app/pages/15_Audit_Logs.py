import os
import sys
import pandas as pd
import streamlit as st

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.database import get_connection
from src.audit_logger import get_audit_logs
from app.components.export_button import render_export_widgets

st.header("📋 System Audit Trail & Event Logs")
st.subheader("Audit System Actions, Override Approvals, Data Imports & Model Changes")

conn = get_connection()

st.markdown("### 🔍 Filter Audit Logs")
action_filter = st.selectbox("Filter by Action", options=["ALL", "LOGIN", "OVERRIDE_CREATED", "OVERRIDE_APPROVED", "OVERRIDE_REJECTED", "MODEL_TRAINED", "MODEL_ACTIVATED", "DATA_UPLOADED", "SETTINGS_UPDATED"])

logs = get_audit_logs(conn, limit=200, action_filter=action_filter)
conn.close()

if logs:
    df_logs = pd.DataFrame(logs)
    st.dataframe(df_logs, use_container_width=True)

    st.markdown("---")
    render_export_widgets(df_logs, "system_audit_logs")
else:
    st.info("No audit logs matching specified filter.")
