import os
import sys
import pandas as pd
import streamlit as st

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.logistics_engine import evaluate_driver_logistics_safety
from src.connectors import GPSConnector
from app.components.export_button import render_export_widgets

st.header("🚛 Driver Safety & Simulated Telemetry Stream")
st.subheader("Fatigue Scoring, Safe Working Hours & Simulated OBD-II GPS Stream")

st.info("ℹ️ Telemetry Stream Note: Real-time driver GPS tracking is powered by a simulated OBD-II adapter (`GPSConnector`).")

gps_conn = GPSConnector()
drivers = [f"D{101 + i}" for i in range(10)]

telemetry_data = [gps_conn.stream_driver_telemetry(d) for d in drivers]
df_telemetry = pd.DataFrame(telemetry_data)

st.markdown("### 📡 Live Vehicle Telemetry Stream")
st.dataframe(df_telemetry, use_container_width=True)

st.markdown("---")
st.markdown("### 🧪 Interactive Driver Dispatch Evaluator")

c1, c2, c3 = st.columns(3)
with c1:
    driver_hours = st.number_input("Driver Current Working Hours", value=44.0, step=1.0)
with c2:
    route_km = st.number_input("Route Distance (KM)", value=180.0, step=10.0)
with c3:
    traffic = st.selectbox("Traffic Level", options=["Low", "Moderate", "Heavy", "Severe Congestion"], index=1)

driver_info = {"driver_id": "D101", "driver_name": "Driver D101", "assigned_hours": driver_hours, "maximum_safe_hours": 50.0}
eval_res = evaluate_driver_logistics_safety(driver_info, route_km, traffic)

d1, d2, d3 = st.columns(3)
with d1:
    st.metric("Projected Total Hours", f"{eval_res['projected_hours']} hrs")
with d2:
    st.metric("Fatigue Risk Score", f"{eval_res['fatigue_risk_score']}%")
with d3:
    if eval_res["safety_status"] == "SAFE":
        st.success("STATUS: SAFE (Dispatch Approved)")
    elif eval_res["safety_status"] == "WARNING":
        st.warning("STATUS: WARNING (Rest Recommended)")
    else:
        st.error("STATUS: BLOCKED (Workload Exceeded)")

st.markdown("---")
render_export_widgets(df_telemetry, "driver_telemetry_logistics_report")
