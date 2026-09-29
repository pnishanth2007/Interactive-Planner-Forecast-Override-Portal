import os
import sys
import pandas as pd
import streamlit as st

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.database import get_connection
from src.active_learning import get_model_history, activate_model_version
from app.components.export_button import render_export_widgets

st.header("⚙️ Model Versioning & Lifecycle Management")
st.subheader("Inspect Machine Learning Model History & Deployment Status")

conn = get_connection()
history = get_model_history(conn)

if history:
    df_models = pd.DataFrame(history)
    st.dataframe(df_models, use_container_width=True)

    st.markdown("---")
    render_export_widgets(df_models, "model_registry_report")
else:
    st.info("No ML models currently registered. Visit the Active Learning page to train models.")

conn.close()
