import os
import sys
import pandas as pd
import streamlit as st

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.preprocessing import clean_data
from src.database import get_connection
from src.active_learning import retrain_model_with_feedback, get_model_history, activate_model_version

st.header("🔄 Active Learning Feedback Loop")
st.subheader("Retrain Forecasting Models Using Historical Successful Planner Overrides")

csv_path = os.path.join(base_dir, "data", "raw", "spare_parts_data.csv")
df_raw = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
df = clean_data(df_raw)

conn = get_connection()

st.markdown("### ⚙️ Retrain Active Learning Model")
st.info("The Active Learning loop extracts historical records where planner overrides improved demand accuracy, weighting those signals into the ML model.")

if st.button("🚀 PREPARE FEEDBACK DATA & RETRAIN MODEL", key="btn_retrain"):
    with st.spinner("Retraining model with feedback signals..."):
        res = retrain_model_with_feedback(df, conn, user_id=st.session_state.get("user_id", "U-ADMIN-01"))
        st.success(f"🎉 Model Retrained Successfully! Version: {res['version']} | MAE: {res['metrics']['MAE']} | WAPE: {res['metrics']['WAPE']}%")

st.markdown("---")
st.markdown("### 📋 Model Version Registry & Activation")
history = get_model_history(conn)

if history:
    history_df = pd.DataFrame(history)
    st.dataframe(history_df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        selected_model_id = st.selectbox("Select Model ID to Activate", options=history_df["model_id"].unique())
    with col2:
        if st.button("⚡ Activate Production Model", key="btn_activate"):
            act_res = activate_model_version(conn, selected_model_id, user_id=st.session_state.get("user_id", "U-ADMIN-01"))
            st.success(act_res["message"])
            st.rerun()
else:
    st.info("No trained models recorded in SQLite yet. Click retrain above to build version 1.")

conn.close()
