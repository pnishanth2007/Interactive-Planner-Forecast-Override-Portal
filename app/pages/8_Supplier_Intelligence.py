import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.preprocessing import clean_data
from src.supplier_engine import evaluate_supplier_intelligence
from app.components.export_button import render_export_widgets

st.header("🏭 Supplier Intelligence & Capacity Allocation")
st.subheader("Capacity Utilization %, Lead Time Risks & Alternate Supplier Recommendations")

csv_path = os.path.join(base_dir, "data", "raw", "spare_parts_data.csv")
df_raw = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
df = clean_data(df_raw)

sup_res = evaluate_supplier_intelligence(df)
sup_df = sup_res["supplier_summary"]

s1, s2, s3 = st.columns(3)
s1.metric("Total Active Suppliers", len(sup_df))
s2.metric("Capacity Overload Count", sup_res["overloaded_suppliers_count"])
s3.metric("High Risk Suppliers", sup_res["high_risk_suppliers_count"])

st.markdown("### 📊 Supplier Allocation & Utilization Table")
st.dataframe(sup_df, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    fig_cap = px.bar(sup_df, x="Supplier_ID", y="Utilization_Pct", color="Supplier_Risk_Level", title="Supplier Capacity Utilization %", template="plotly_dark")
    st.plotly_chart(fig_cap, use_container_width=True)

with col2:
    fig_lead = px.bar(sup_df, x="Supplier_ID", y="Avg_Lead_Time", color="Avg_Service_Level", title="Average Lead Time (Days) vs Service Level", template="plotly_dark")
    st.plotly_chart(fig_lead, use_container_width=True)

st.markdown("---")
render_export_widgets(sup_df, "supplier_intelligence_report")
