"""
Unit tests for Authentication, Password Hashing, and Role Permissions.
"""

import pytest
from src.auth import hash_password, verify_password, get_role_permissions

def test_password_hashing():
    pw = "secret123"
    h1, s1 = hash_password(pw)
    assert h1 != pw
    assert len(s1) == 32
    assert verify_password(pw, h1, s1) is True
    assert verify_password("wrongpass", h1, s1) is False

def test_role_permissions():
    admin_p = get_role_permissions("Admin")
    assert admin_p["can_manage_users"] is True
    assert admin_p["max_override_pct"] == 1000.0

    junior_p = get_role_permissions("Junior Planner")
    assert junior_p["can_approve_override"] is False
    assert junior_p["max_override_pct"] == 20.0
