import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.preprocessing import clean_data
from src.forecasting import evaluate_all_models
from app.components.export_button import render_export_widgets

st.header("📈 Demand Forecasting & Model Comparison Framework")
st.subheader("Multi-Model Validation Matrix & Accuracy Leaderboard")

@st.cache_data
def get_forecasting_data():
    csv_path = os.path.join(base_dir, "data", "raw", "spare_parts_data.csv")
    df_raw = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
    df_c = clean_data(df_raw)
    comp_matrix = evaluate_all_models(df_c)
    return df_c, comp_matrix

df_clean, comp_df = get_forecasting_data()

st.markdown("### 🏆 Forecasting Models Performance Matrix")
st.dataframe(comp_df, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    fig_wape = px.bar(comp_df, x="Model", y="WAPE", color="WAPE", color_continuous_scale="Reds_r", title="WAPE Error (%) by Model (Lower is Better)", template="plotly_dark")
    st.plotly_chart(fig_wape, use_container_width=True)

with col2:
    fig_mae = px.bar(comp_df, x="Model", y="MAE", color="MAE", color_continuous_scale="Oranges_r", title="Mean Absolute Error (MAE) Comparison", template="plotly_dark")
    st.plotly_chart(fig_mae, use_container_width=True)

st.markdown("---")
render_export_widgets(comp_df, "forecasting_model_comparison")
