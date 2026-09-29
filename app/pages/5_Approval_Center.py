import os
import sys
import pandas as pd
import streamlit as st

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.database import get_connection
from src.approval_engine import get_pending_approvals, approve_override, reject_override

st.header("🚦 Manager Approval Center")
st.subheader("Review Pending Overrides Exceeding Planner Role Limits")

conn = get_connection()
pending_list = get_pending_approvals(conn)

st.markdown(f"### 📋 Pending Requests Queue ({len(pending_list)})")

if pending_list:
    for item in pending_list:
        with st.expander(f"Override #{item['override_id']} | Part {item['part_id']} | Requested by {item['requested_by']} ({item['planner_role']})", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Baseline Forecast:** {item['baseline_forecast']} units")
                st.write(f"**Requested Override:** {item['override_quantity']:+} units ({item['override_pct']}%)")
                st.write(f"**Final Demand:** {item['final_demand']} units")
            with col2:
                st.write(f"**Reason Code:** {item['reason_code']}")
                st.write(f"**Comment:** {item['reason_comment']}")
                st.write(f"**Requested At:** {item['timestamp']}")
            with col3:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✅ Approve", key=f"app_{item['override_id']}"):
                        res = approve_override(conn, item['override_id'], st.session_state.get("user_id", "U-MANAGER-01"))
                        st.success(res["message"])
                        st.rerun()
                with btn_col2:
                    rej_reason = st.text_input("Rejection Reason", key=f"txt_rej_{item['override_id']}")
                    if st.button("❌ Reject", key=f"rej_{item['override_id']}"):
                        res = reject_override(conn, item['override_id'], st.session_state.get("user_id", "U-MANAGER-01"), rej_reason)
                        if res["success"]:
                            st.warning(res["message"])
                            st.rerun()
                        else:
                            st.error(res["error"])
else:
    st.success("🎉 All overrides have been processed. No pending approval requests!")

conn.close()
