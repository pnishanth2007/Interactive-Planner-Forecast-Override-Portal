import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.preprocessing import clean_data
from src.anomaly_engine import detect_irregular_failure_patterns, get_failure_risk_summary
from app.components.export_button import render_export_widgets

st.header("⚡ Failure Pattern Analysis & Anomaly Detection")
st.subheader("Detect Irregular Spikes, Intermittent Failures & Equipment Cluster Risks")

csv_path = os.path.join(base_dir, "data", "raw", "spare_parts_data.csv")
df_raw = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
df = clean_data(df_raw)

df_anomaly = detect_irregular_failure_patterns(df)
risk_summary = get_failure_risk_summary(df_anomaly)

a1, a2, a3 = st.columns(3)
a1.metric("Total Anomaly Events", risk_summary["total_anomalies"])
a2.metric("Critical Spikes", risk_summary["critical_count"])
a3.metric("High Risk Anomalies", risk_summary["high_risk_count"])

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    fig_risk = px.histogram(df_anomaly, x="Risk_Level", color="Risk_Level", title="Anomaly Event Frequency by Risk Level", template="plotly_dark")
    st.plotly_chart(fig_risk, use_container_width=True)

with col2:
    fig_scatter = px.scatter(df_anomaly.sample(min(800, len(df_anomaly))), x="Historical_Demand", y="Actual_Demand", color="Risk_Level", hover_data=["Part_Name", "Equipment_Type"], title="Historical Demand vs Actual Demand Anomaly Distribution", template="plotly_dark")
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("### 📋 Top Critical Anomaly Events")
st.dataframe(df_anomaly[df_anomaly["Risk_Level"] == "Critical"][["Record_ID", "Part_Name", "Equipment_Type", "Demand_Pattern", "Historical_Demand", "Actual_Demand", "Deviation_Pct", "Risk_Level"]].head(15), use_container_width=True)

st.markdown("---")
render_export_widgets(df_anomaly, "failure_pattern_anomaly_report")
