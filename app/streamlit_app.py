"""
Spare Parts Override Learning System — Main Enterprise Portal
Integrates multi-page sidebar navigation, user session authentication, and database initialization.
"""

import os
import sys
import pandas as pd
import streamlit as st

# Add root directory to path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.database import init_db, seed_users_and_drivers, get_connection
from src.data_generator import generate_spare_parts_data
from src.preprocessing import clean_data
from src.database import populate_db_from_dataframe
from app.components.auth_widget import render_login_sidebar

st.set_page_config(
    page_title="Spare Parts Override Learning System",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    .stMetric {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
    }
    .stMetricValue {
        color: #38BDF8 !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# Ensure Database & Raw Data exist
db_path = os.path.join(base_dir, "database", "spare_parts.db")
csv_path = os.path.join(base_dir, "data", "raw", "spare_parts_data.csv")

if not os.path.exists(csv_path):
    df_raw = generate_spare_parts_data(10000)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df_raw.to_csv(csv_path, index=False)
    df_clean = clean_data(df_raw)
    populate_db_from_dataframe(df_clean, db_path)
else:
    if not os.path.exists(db_path):
        df_raw = pd.read_csv(csv_path)
        df_clean = clean_data(df_raw)
        populate_db_from_dataframe(df_clean, db_path)
    else:
        init_db(db_path)
        seed_users_and_drivers(db_path)

# Sidebar Auth & Branding
st.sidebar.image("https://img.icons8.com/isometric-line/100/38bdf8/gear.png", width=70)
st.sidebar.title("Spare Parts Platform")
st.sidebar.caption("Enterprise Demand Planning v2.0 (100% Production Platform)")

render_login_sidebar(db_path)

st.title("⚙️ Spare-Parts Demand Planning & Override Intelligence Platform")
st.subheader("Welcome to the Production Enterprise Demand Planning Portal")

st.markdown("""
Select a module from the sidebar navigation menu:
- 📊 **Executive Dashboard** — High-level KPI metrics & accuracy visualizations
- 📈 **Demand Forecasting** — Multi-model validation matrix & WAPE/MAE leaderboards
- ✍️ **Planner Workbench** — Interactive planner override portal with real-time constraint validation
- 📑 **Override Management** — Comprehensive audit trail of submitted demand overrides
- 🚦 **Approval Center** — Manager sign-off queue for overrides exceeding role limits
- 🛡️ **Constraint Monitor** — Operational failure case tester & hard rule evaluator
- 📦 **Inventory Intelligence** — Reorder point (ROP) calculations & stock categorization
- 🏭 **Supplier Intelligence** — Supplier capacity utilization & lead-time risk tracking
- ⚡ **Failure Pattern Analysis** — Detection of irregular demand spikes and equipment clusters
- 🚛 **Driver & Logistics Safety** — Driver fatigue scoring & simulated GPS telemetry stream
- 🧠 **Override Intelligence** — Historical override pattern analysis & reason code rankings
- 🔄 **Active Learning** — Model retraining using successful planner override feedback signals
- ⚙️ **Model Management** — Machine learning model registry & deployment status
- 📤 **Data Upload** — Enterprise CSV/Excel file validation & ingestion portal
- 📋 **Audit Logs** — System activity audit trails
- 🛠️ **System Settings** — DB-backed role limits & operational setting controls
""")

conn = get_connection(db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM forecasts;")
total_f = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM overrides;")
total_o = cursor.fetchone()[0]
conn.close()

col1, col2, col3 = st.columns(3)
col1.metric("Database Forecast Records", f"{total_f:,}")
col2.metric("Recorded Overrides", f"{total_o:,}")
col3.metric("System Status", "ONLINE (100% Platform)")
