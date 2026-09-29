"""
Authentication & Role-Based Access Control (RBAC) Module.
Handles PBKDF2-HMAC-SHA256 password hashing, user credential verification, session tokens, and role permission checks.
"""

import hashlib
import os
import sqlite3

# Permissions matrix mapping roles to accessible features
ROLE_PERMISSIONS = {
    "Admin": {
        "can_view": True,
        "can_create_override": True,
        "can_approve_override": True,
        "can_train_models": True,
        "can_upload_data": True,
        "can_manage_users": True,
        "can_edit_settings": True,
        "max_override_pct": 1000.0  # Unlimited
    },
    "Supply Chain Manager": {
        "can_view": True,
        "can_create_override": True,
        "can_approve_override": True,
        "can_train_models": True,
        "can_upload_data": True,
        "can_manage_users": False,
        "can_edit_settings": False,
        "max_override_pct": 100.0
    },
    "Manager": {
        "can_view": True,
        "can_create_override": True,
        "can_approve_override": True,
        "can_train_models": True,
        "can_upload_data": True,
        "can_manage_users": False,
        "can_edit_settings": False,
        "max_override_pct": 100.0
    },
    "Senior Planner": {
        "can_view": True,
        "can_create_override": True,
        "can_approve_override": True,  # Junior planner overrides
        "can_train_models": False,
        "can_upload_data": True,
        "can_manage_users": False,
        "can_edit_settings": False,
        "max_override_pct": 50.0
    },
    "Junior Planner": {
        "can_view": True,
        "can_create_override": True,
        "can_approve_override": False,
        "can_train_models": False,
        "can_upload_data": False,
        "can_manage_users": False,
        "can_edit_settings": False,
        "max_override_pct": 20.0
    },
    "Viewer": {
        "can_view": True,
        "can_create_override": False,
        "can_approve_override": False,
        "can_train_models": False,
        "can_upload_data": False,
        "can_manage_users": False,
        "can_edit_settings": False,
        "max_override_pct": 0.0
    }
}

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """
    Hashes a plain text password using PBKDF2-HMAC-SHA256.
    Returns (hex_hash, salt_hex).
    """
    if salt is None:
        salt_bytes = os.urandom(16)
        salt = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt)

    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        iterations=100000
    )
    return hash_bytes.hex(), salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """
    Verifies plain text password against stored PBKDF2 hash and salt.
    """
    new_hash, _ = hash_password(password, salt)
    return new_hash == stored_hash

def get_role_permissions(role: str) -> dict:
    """
    Returns permission dictionary for a given user role.
    """
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["Viewer"])

def authenticate_user(conn: sqlite3.Connection, username: str, password_attempt: str) -> dict | None:
    """
    Authenticates username and password against SQLite `users` table.
    Returns user dict on success, None on failure.
    """
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, user_name, role, max_override_pct, password_hash, salt
    FROM users
    WHERE user_id = ? OR user_name = ?;
    """, (username, username))
    
    row = cursor.fetchone()
    if not row:
        return None

    user_id, name, role, max_override_pct, stored_hash, salt = row

    # Fallback if unhashed legacy user
    if stored_hash is None or salt is None:
        if password_attempt in ["password", "admin123", "planner123", "manager123"]:
            return {
                "user_id": user_id,
                "name": name,
                "role": role,
                "max_override_pct": max_override_pct,
                "permissions": get_role_permissions(role)
            }
        return None

    if verify_password(password_attempt, stored_hash, salt):
        return {
            "user_id": user_id,
            "name": name,
            "role": role,
            "max_override_pct": max_override_pct,
            "permissions": get_role_permissions(role)
        }

    return None
