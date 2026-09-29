"""
Approval Workflow & Authorization Management Engine.
Manages pending override requests, manager sign-offs, rejections, auto-approvals, and approval history.
"""

import sqlite3
from datetime import datetime
from src.audit_logger import log_action

def get_pending_approvals(conn: sqlite3.Connection) -> list:
    """
    Retrieves all pending override approval requests.
    """
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.approval_id, a.override_id, a.requested_by, a.status, a.timestamp,
           o.record_id, o.planner_role, o.override_quantity, o.override_pct, o.reason_code, o.reason_comment, o.final_demand,
           f.part_id, f.baseline_forecast, f.actual_demand
    FROM approvals a
    JOIN overrides o ON a.override_id = o.override_id
    JOIN forecasts f ON o.record_id = f.record_id
    WHERE a.status = 'PENDING' OR o.approval_status = 'PENDING APPROVAL'
    ORDER BY a.approval_id DESC;
    """)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def approve_override(conn: sqlite3.Connection, override_id: int, approver_id: str) -> dict:
    """
    Approves a pending override request. Updates DB tables `overrides`, `approvals`, and logs audit event.
    """
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE overrides
    SET approval_status = 'APPROVED', approval_time = ?
    WHERE override_id = ?;
    """, (now_str, override_id))

    cursor.execute("""
    UPDATE approvals
    SET status = 'APPROVED', approver_id = ?, timestamp = ?
    WHERE override_id = ?;
    """, (approver_id, now_str, override_id))

    conn.commit()
    log_action(conn, approver_id, "OVERRIDE_APPROVED", "overrides", str(override_id), old_value="PENDING APPROVAL", new_value="APPROVED")

    return {"success": True, "message": f"Override #{override_id} approved by {approver_id}."}

def reject_override(conn: sqlite3.Connection, override_id: int, approver_id: str, rejection_reason: str) -> dict:
    """
    Rejects a pending override request with a required rejection reason.
    """
    if not rejection_reason or rejection_reason.strip() == "":
        return {"success": False, "error": "Rejection reason is mandatory."}

    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE overrides
    SET approval_status = 'REJECTED', approval_time = ?
    WHERE override_id = ?;
    """, (now_str, override_id))

    cursor.execute("""
    UPDATE approvals
    SET status = 'REJECTED', approver_id = ?, rejection_reason = ?, timestamp = ?
    WHERE override_id = ?;
    """, (approver_id, rejection_reason, now_str, override_id))

    conn.commit()
    log_action(conn, approver_id, "OVERRIDE_REJECTED", "overrides", str(override_id), old_value="PENDING APPROVAL", new_value=f"REJECTED: {rejection_reason}")

    return {"success": True, "message": f"Override #{override_id} rejected."}
