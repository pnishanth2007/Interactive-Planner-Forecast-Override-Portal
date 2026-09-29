import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.preprocessing import clean_data
from src.evaluation import evaluate_demand_outcomes, analyze_error_patterns
from src.learning import analyze_override_learning
from app.components.export_button import render_export_widgets

st.header("📊 Executive Dashboard")
st.subheader("Enterprise Operational Metrics & Override Learning Overview")

@st.cache_data
def get_cached_dashboard_data():
    csv_path = os.path.join(base_dir, "data", "raw", "spare_parts_data.csv")
    if os.path.exists(csv_path):
        df_raw = pd.read_csv(csv_path)
    else:
        from src.data_generator import generate_spare_parts_data
        df_raw = generate_spare_parts_data(10000)
    df_c = clean_data(df_raw)
    df_ev, sum_m = evaluate_demand_outcomes(df_c)
    return df_ev, sum_m

df_eval, summary = get_cached_dashboard_data()

# KPI Metric Cards Row 1
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Parts", f"{df_eval['Part_ID'].nunique()}")
k2.metric("Total Forecasts", f"{len(df_eval):,}")
k3.metric("Total Overrides", f"{summary['Total_Overrides']:,}")
k4.metric("Override Success Rate", f"{summary['Override_Success_Rate_Pct']:.1f}%")
k5.metric("Baseline MAE", f"{summary['Baseline_MAE']:.2f}")

# KPI Metric Cards Row 2
k6, k7, k8, k9, k10 = st.columns(5)
k6.metric("Post-Override MAE", f"{summary['Override_MAE']:.2f}", delta=f"-{summary['MAE_Improvement_Pct']:.1f}% Error")
k7.metric("Service Level", f"{summary['Service_Level_Pct']:.1f}%")
k8.metric("Stockout Rate", f"{summary['Stockout_Rate_Pct']:.1f}%")
k9.metric("Total Logistics Cost", f"${df_eval['Estimated_Cost'].sum()/1e6:.2f}M")
k10.metric("Total Emissions", f"{df_eval['Estimated_Emissions'].sum()/1e3:.1f} Tons")

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    fig1 = go.Figure()
    fig1.add_trace(go.Histogram(x=df_eval["Baseline_Error"], name="Baseline Error", marker_color="#EF4444", opacity=0.75, nbinsx=30))
    fig1.add_trace(go.Histogram(x=df_eval["Override_Error"], name="Override Error", marker_color="#10B981", opacity=0.75, nbinsx=30))
    fig1.update_layout(title="Baseline vs Override Error Distribution", barmode="overlay", template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    learning_res = analyze_override_learning(df_eval)
    reason_df = learning_res.get("reason_learning", pd.DataFrame())
    if not reason_df.empty:
        fig2 = px.bar(reason_df, x="Success_Rate_Pct", y="Override_Reason", orientation="h", color="Success_Rate_Pct", color_continuous_scale="Teal", title="Override Success Rate by Reason Code", template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("### 🚨 Top Failure Risks & Error Drivers")
err_patterns = analyze_error_patterns(df_eval)
c_e1, c_e2 = st.columns(2)
with c_e1:
    st.caption("Worst Performing Parts")
    st.dataframe(err_patterns["worst_parts"], use_container_width=True)
with c_e2:
    st.caption("Worst Performing Equipment Types")
    st.dataframe(err_patterns["worst_equipment"], use_container_width=True)

st.markdown("---")
render_export_widgets(df_eval, "executive_dashboard_report")
