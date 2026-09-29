import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.preprocessing import clean_data
from src.inventory_engine import calculate_inventory_position, get_inventory_recommendations_summary
from app.components.export_button import render_export_widgets

st.header("📦 Inventory Intelligence & Stock Optimization")
st.subheader("Reorder Point (ROP) Calculations & Stock Categorization")

csv_path = os.path.join(base_dir, "data", "raw", "spare_parts_data.csv")
df_raw = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
df = clean_data(df_raw)

df_inv = calculate_inventory_position(df)
inv_summary = get_inventory_recommendations_summary(df_inv)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Critical Stock Parts", inv_summary["critical_parts_count"])
c2.metric("Reorder Needed", inv_summary["reorder_needed_count"])
c3.metric("Recommended Reorder Units", f"{inv_summary['total_recommended_reorder_units']:,}")
c4.metric("Healthy Stock Count", inv_summary["status_counts"].get("Healthy Stock", 0))

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    fig_status = px.pie(names=list(inv_summary["status_counts"].keys()), values=list(inv_summary["status_counts"].values()), title="Inventory Health Status Share", template="plotly_dark")
    st.plotly_chart(fig_status, use_container_width=True)

with col2:
    st.markdown("### 🚨 Top Reorder Recommendations")
    st.dataframe(inv_summary["top_reorder_parts"], use_container_width=True)

st.markdown("---")
render_export_widgets(df_inv, "inventory_optimization_report")
