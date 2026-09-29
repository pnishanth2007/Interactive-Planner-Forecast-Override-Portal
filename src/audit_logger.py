"""
Audit Logger Module.
Records all system events, planner actions, override approvals, model training runs, and settings changes.
"""

import sqlite3
from datetime import datetime
import json

def log_action(conn: sqlite3.Connection, user_id: str, action: str, entity: str = None, entity_id: str = None, old_value=None, new_value=None, status: str = "SUCCESS"):
    """
    Logs an auditable system action into SQLite `audit_logs` table.
    """
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    old_str = json.dumps(old_value) if isinstance(old_value, (dict, list)) else (str(old_value) if old_value is not None else None)
    new_str = json.dumps(new_value) if isinstance(new_value, (dict, list)) else (str(new_value) if new_value is not None else None)

    cursor.execute("""
    INSERT INTO audit_logs (user_id, timestamp, action, entity, entity_id, old_value, new_value, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (user_id, now_str, action, entity, entity_id, old_str, new_str, status))

    conn.commit()

def get_audit_logs(conn: sqlite3.Connection, limit: int = 200, action_filter: str = None) -> list:
    """
    Retrieves recent audit log records.
    """
    cursor = conn.cursor()
    if action_filter and action_filter != "ALL":
        cursor.execute("""
        SELECT log_id, user_id, timestamp, action, entity, entity_id, old_value, new_value, status
        FROM audit_logs
        WHERE action = ?
        ORDER BY log_id DESC
        LIMIT ?;
        """, (action_filter, limit))
    else:
        cursor.execute("""
        SELECT log_id, user_id, timestamp, action, entity, entity_id, old_value, new_value, status
        FROM audit_logs
        ORDER BY log_id DESC
        LIMIT ?;
        """, (limit,))

    rows = cursor.fetchall()
    return [dict(row) for row in rows]
