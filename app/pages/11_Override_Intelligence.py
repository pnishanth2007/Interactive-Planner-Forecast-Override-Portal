import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.preprocessing import clean_data
from src.evaluation import evaluate_demand_outcomes
from src.learning import analyze_override_learning
from app.components.export_button import render_export_widgets

st.header("🧠 Override Intelligence & Pattern Insights")
st.subheader("Factual Historical Success Rates across Reasons, Parts, Equipment & Roles")

csv_path = os.path.join(base_dir, "data", "raw", "spare_parts_data.csv")
df_raw = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
df = clean_data(df_raw)
df_eval, _ = evaluate_demand_outcomes(df)

learning_data = analyze_override_learning(df_eval)

most_succ = learning_data.get("most_successful_reason", {})
least_succ = learning_data.get("least_successful_reason", {})

l1, l2, l3 = st.columns(3)
l1.success(f"🏆 **Best Reason Code**\n\n**{most_succ.get('code')}** — {most_succ.get('description')}\n\nSuccess Rate: **{most_succ.get('success_rate')}%**")
l2.error(f"⚠️ **Least Successful Reason**\n\n**{least_succ.get('code')}** — {least_succ.get('description')}\n\nSuccess Rate: **{least_succ.get('success_rate')}%**")
review_df = learning_data.get("reasons_requiring_review", pd.DataFrame())
l3.warning(f"🔍 **Reasons Requiring Review**\n\n**{len(review_df)} code(s)** flagged with success rate < 55%.")

st.markdown("---")
st.markdown("### 📊 Success Rate Intelligence Table")
reason_df = learning_data.get("reason_learning", pd.DataFrame())
st.dataframe(reason_df, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    fig_imp = px.bar(reason_df, x="Override_Reason", y="Avg_Improvement_Pct", color="Avg_Improvement_Pct", title="Average Error Improvement (%) by Reason Code", template="plotly_dark")
    st.plotly_chart(fig_imp, use_container_width=True)

with col2:
    eq_df = learning_data.get("equipment_learning", pd.DataFrame())
    fig_eq = px.bar(eq_df, x="Equipment_Type", y="Success_Rate_Pct", color="Success_Rate_Pct", title="Override Success Rate (%) by Equipment Type", template="plotly_dark")
    st.plotly_chart(fig_eq, use_container_width=True)

st.markdown("---")
render_export_widgets(reason_df, "override_intelligence_report")
