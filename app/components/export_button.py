"""
Streamlit Export Buttons UI Component.
Renders reusable CSV and Excel download widgets.
"""

import streamlit as st
import pandas as pd
from src.exporter import generate_csv_bytes, generate_excel_bytes

def render_export_widgets(df: pd.DataFrame, filename_prefix: str = "report"):
    """
    Renders side-by-side CSV and Excel download buttons.
    """
    col1, col2 = st.columns(2)

    csv_data = generate_csv_bytes(df)
    excel_data = generate_excel_bytes(df)

    with col1:
        st.download_button(
            label="📥 Download CSV Report",
            data=csv_data,
            file_name=f"{filename_prefix}.csv",
            mime="text/csv",
            key=f"dl_csv_{filename_prefix}"
        )

    with col2:
        st.download_button(
            label="📊 Download Excel Report",
            data=excel_data,
            file_name=f"{filename_prefix}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_excel_{filename_prefix}"
        )
