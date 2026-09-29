import os
import sys
import pandas as pd
import streamlit as st

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.ingestion import process_file_upload
from src.database import get_connection, populate_db_from_dataframe
from src.audit_logger import log_action

st.header("📤 Enterprise Data Upload & Validation Portal")
st.subheader("Upload CSV or Excel Spare-Parts Demand Records for Automated Ingestion")

uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    st.markdown("### 🔍 Validation Results")
    df_clean, summary = process_file_upload(uploaded_file, base_dir)

    v1, v2, v3 = st.columns(3)
    v1.metric("Total Rows Detected", summary["rows_total"])
    v2.metric("Valid Rows", summary["rows_valid"])
    v3.metric("Invalid Rows", summary["rows_invalid"])

    if summary["is_valid"]:
        st.success("🎉 Validation Passed! All required schema columns and value bounds are valid.")
        
        if summary["warnings"]:
            for w in summary["warnings"]:
                st.warning(f"⚠️ {w}")

        st.markdown("### 📋 Data Preview")
        st.dataframe(df_clean.head(10), use_container_width=True)

        if st.button("🚀 Import Validated Dataset Into Database", key="btn_import"):
            conn = get_connection()
            populate_db_from_dataframe(df_clean)
            log_action(conn, st.session_state.get("user_id", "U-ADMIN-01"), "DATA_UPLOADED", "file", uploaded_file.name, new_value=f"{len(df_clean)} rows imported")
            conn.close()
            st.toast("Dataset successfully imported into SQLite database!", icon="💾")
    else:
        st.error("❌ Validation Failed! Fix the following issues before importing:")
        for err in summary["errors"]:
            st.error(f"• {err}")
