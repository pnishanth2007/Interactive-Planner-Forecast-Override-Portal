"""
Streamlit Authentication & Navigation Widget.
Handles user session state, login/logout interface, role badges, and access control checks.
"""

import streamlit as st
from src.database import get_connection
from src.auth import authenticate_user

def init_session_state():
    """Initializes Streamlit authentication session state."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["user_id"] = "U-ADMIN-01"
        st.session_state["user_name"] = "System Administrator"
        st.session_state["role"] = "Admin"
        st.session_state["permissions"] = {
            "can_view": True,
            "can_create_override": True,
            "can_approve_override": True,
            "can_train_models": True,
            "can_upload_data": True,
            "can_manage_users": True,
            "can_edit_settings": True,
            "max_override_pct": 1000.0
        }

def render_login_sidebar(db_path=None):
    """
    Renders login/logout controls in Streamlit sidebar.
    """
    init_session_state()

    st.sidebar.markdown("### 🔒 User Session & RBAC")
    
    if st.session_state["authenticated"]:
        st.sidebar.success(f"Logged in: **{st.session_state['user_name']}**")
        st.sidebar.caption(f"Role: **{st.session_state['role']}** (Limit: {st.session_state['permissions']['max_override_pct']}%)")
        if st.sidebar.button("Logout", key="btn_logout"):
            st.session_state["authenticated"] = False
            st.session_state["role"] = "Viewer"
            st.rerun()
    else:
        with st.sidebar.expander("👤 User Login / Switch Role", expanded=False):
            username = st.text_input("Username", value="admin123", key="txt_user")
            password = st.text_input("Password", value="admin123", type="password", key="txt_pass")
            
            if st.button("Sign In", key="btn_login"):
                conn = get_connection(db_path)
                user_info = authenticate_user(conn, username, password)
                conn.close()

                if user_info:
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = user_info["user_id"]
                    st.session_state["user_name"] = user_info["name"]
                    st.session_state["role"] = user_info["role"]
                    st.session_state["permissions"] = user_info["permissions"]
                    st.success(f"Welcome back, {user_info['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

def check_permission(permission_key: str) -> bool:
    """Checks if currently logged in user has specified permission."""
    init_session_state()
    return st.session_state["permissions"].get(permission_key, False)
