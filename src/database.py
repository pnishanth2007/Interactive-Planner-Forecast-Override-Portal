"""
Database Module for SQLite storage, migrations, and transactional queries.
Supports fully normalized relational schema: users, roles, parts, equipment, suppliers, demand_history,
forecasts, planners, override_reasons, overrides, constraints, approvals, drivers, deliveries, outcomes,
models, model_metrics, telemetry, audit_logs, and settings.
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime
from src.auth import hash_password

def get_db_path(base_dir=None):
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(base_dir, "database")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "spare_parts.db")

def get_connection(db_path=None):
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def safe_add_column(cursor, table_name, column_name, column_type):
    """
    Safely adds a column to an existing table if it does not already exist.
    """
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [row[1] for row in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};")

def init_db(db_path=None):
    """
    Initializes or migrates SQLite database schema with foreign keys, indexes, and constraints.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        user_name TEXT NOT NULL,
        role TEXT NOT NULL,
        max_override_pct REAL NOT NULL
    );
    """)
    safe_add_column(cursor, "users", "password_hash", "TEXT")
    safe_add_column(cursor, "users", "salt", "TEXT")

    # 2. Roles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT UNIQUE NOT NULL,
        max_override_pct REAL NOT NULL,
        can_approve INTEGER NOT NULL DEFAULT 0,
        description TEXT
    );
    """)

    # 3. Parts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parts (
        part_id TEXT PRIMARY KEY,
        part_name TEXT NOT NULL,
        inventory_level INTEGER NOT NULL,
        safety_stock INTEGER NOT NULL,
        supplier_capacity INTEGER NOT NULL,
        lead_time_days INTEGER NOT NULL
    );
    """)
    safe_add_column(cursor, "parts", "category", "TEXT DEFAULT 'General'")
    safe_add_column(cursor, "parts", "unit_cost", "REAL DEFAULT 100.0")
    safe_add_column(cursor, "parts", "reorder_point", "INTEGER DEFAULT 15")
    safe_add_column(cursor, "parts", "supplier_id", "TEXT DEFAULT 'SUP-101'")

    # 4. Equipment Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment (
        equipment_id TEXT PRIMARY KEY,
        equipment_type TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        region TEXT NOT NULL
    );
    """)
    safe_add_column(cursor, "equipment", "installation_year", "INTEGER DEFAULT 2020")
    safe_add_column(cursor, "equipment", "failure_frequency_score", "REAL DEFAULT 1.0")

    # 5. Suppliers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id TEXT PRIMARY KEY,
        supplier_name TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        current_allocation INTEGER NOT NULL DEFAULT 0,
        remaining_capacity INTEGER NOT NULL,
        lead_time_days INTEGER NOT NULL,
        reliability_score REAL NOT NULL DEFAULT 95.0,
        location TEXT DEFAULT 'Global'
    );
    """)

    # 6. Forecasts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS forecasts (
        forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT UNIQUE NOT NULL,
        part_id TEXT NOT NULL,
        equipment_id TEXT NOT NULL,
        failure_date TEXT NOT NULL,
        failure_type TEXT,
        demand_pattern TEXT,
        historical_demand INTEGER NOT NULL,
        baseline_forecast INTEGER NOT NULL,
        actual_demand INTEGER NOT NULL,
        forecast_error INTEGER NOT NULL,
        FOREIGN KEY(part_id) REFERENCES parts(part_id),
        FOREIGN KEY(equipment_id) REFERENCES equipment(equipment_id)
    );
    """)
    safe_add_column(cursor, "forecasts", "advanced_forecast", "INTEGER DEFAULT 0")
    safe_add_column(cursor, "forecasts", "failure_severity", "TEXT DEFAULT 'Moderate'")

    # 7. Planners Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planners (
        planner_id TEXT PRIMARY KEY,
        planner_name TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        active_status TEXT DEFAULT 'ACTIVE'
    );
    """)

    # 8. Override Reasons Table (DB-backed master)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS override_reasons (
        reason_code TEXT PRIMARY KEY,
        reason_name TEXT NOT NULL,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        default_category TEXT DEFAULT 'Field Context'
    );
    """)

    # 9. Overrides Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS overrides (
        override_id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT NOT NULL,
        planner_id TEXT NOT NULL,
        planner_role TEXT NOT NULL,
        override_quantity INTEGER NOT NULL,
        reason_code TEXT,
        reason_comment TEXT,
        final_demand INTEGER NOT NULL,
        approval_status TEXT NOT NULL,
        approval_time TEXT NOT NULL,
        FOREIGN KEY(record_id) REFERENCES forecasts(record_id)
    );
    """)
    safe_add_column(cursor, "overrides", "direction", "TEXT DEFAULT 'INCREASE'")
    safe_add_column(cursor, "overrides", "override_pct", "REAL DEFAULT 0.0")

    # 10. Constraints Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS constraints (
        constraint_id INTEGER PRIMARY KEY AUTOINCREMENT,
        override_id INTEGER NOT NULL,
        hard_status TEXT NOT NULL,
        soft_status TEXT NOT NULL,
        violation_details TEXT,
        FOREIGN KEY(override_id) REFERENCES overrides(override_id)
    );
    """)
    safe_add_column(cursor, "constraints", "human_explanation", "TEXT")

    # 11. Approvals Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS approvals (
        approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
        override_id INTEGER NOT NULL,
        requested_by TEXT NOT NULL,
        approver_id TEXT,
        status TEXT NOT NULL DEFAULT 'PENDING',
        rejection_reason TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY(override_id) REFERENCES overrides(override_id)
    );
    """)

    # 12. Drivers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drivers (
        driver_id TEXT PRIMARY KEY,
        driver_name TEXT NOT NULL,
        available_hours REAL NOT NULL,
        assigned_hours REAL NOT NULL,
        maximum_safe_hours REAL NOT NULL,
        workload_percentage REAL NOT NULL,
        safety_status TEXT NOT NULL
    );
    """)
    safe_add_column(cursor, "drivers", "fatigue_score", "REAL DEFAULT 10.0")

    # 13. Deliveries Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deliveries (
        delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT NOT NULL,
        driver_id TEXT NOT NULL,
        vehicle_type TEXT NOT NULL,
        delivery_distance_km REAL,
        delivery_time_hours REAL,
        estimated_cost REAL,
        estimated_emissions REAL,
        FOREIGN KEY(record_id) REFERENCES forecasts(record_id),
        FOREIGN KEY(driver_id) REFERENCES drivers(driver_id)
    );
    """)
    safe_add_column(cursor, "deliveries", "traffic_level", "TEXT DEFAULT 'Moderate'")

    # 14. Outcomes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS outcomes (
        outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT UNIQUE NOT NULL,
        baseline_error REAL NOT NULL,
        override_error REAL NOT NULL,
        override_improved TEXT NOT NULL,
        stockout_flag INTEGER NOT NULL,
        emergency_order_flag INTEGER NOT NULL,
        service_level REAL NOT NULL,
        FOREIGN KEY(record_id) REFERENCES forecasts(record_id)
    );
    """)
    safe_add_column(cursor, "outcomes", "error_improvement", "REAL DEFAULT 0.0")

    # 15. Models Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS models (
        model_id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT NOT NULL,
        version TEXT NOT NULL,
        training_date TEXT NOT NULL,
        training_rows INTEGER NOT NULL,
        mae REAL NOT NULL,
        rmse REAL NOT NULL,
        mape REAL NOT NULL,
        wape REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'INACTIVE'
    );
    """)

    # 16. Model Metrics Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_metrics (
        metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_id INTEGER NOT NULL,
        metric_name TEXT NOT NULL,
        metric_value REAL NOT NULL,
        evaluation_date TEXT NOT NULL,
        FOREIGN KEY(model_id) REFERENCES models(model_id)
    );
    """)

    # 17. Telemetry Table (GPS stream)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telemetry (
        telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        speed_kmh REAL NOT NULL,
        driving_hours REAL NOT NULL,
        traffic_condition TEXT NOT NULL,
        status_flag TEXT NOT NULL,
        FOREIGN KEY(driver_id) REFERENCES drivers(driver_id)
    );
    """)

    # 18. Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        action TEXT NOT NULL,
        entity TEXT,
        entity_id TEXT,
        old_value TEXT,
        new_value TEXT,
        status TEXT NOT NULL DEFAULT 'SUCCESS'
    );
    """)

    # 19. Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        updated_by TEXT DEFAULT 'SYSTEM'
    );
    """)

    conn.commit()
    conn.close()

def seed_users_and_drivers(db_path=None):
    """
    Seeds default user profiles with hashed passwords, roles, reasons, suppliers, and settings.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Seed Roles
    roles = [
        ("Admin", 1000.0, 1, "Full System Administrator"),
        ("Supply Chain Manager", 100.0, 1, "Manager - Max 100% Override Authority"),
        ("Senior Planner", 50.0, 1, "Senior Planner - Max 50% Override Authority"),
        ("Junior Planner", 20.0, 0, "Junior Planner - Max 20% Override Authority"),
        ("Viewer", 0.0, 0, "Read-Only Dashboard Viewer")
    ]
    for r in roles:
        cursor.execute("""
        INSERT OR IGNORE INTO roles (role_name, max_override_pct, can_approve, description)
        VALUES (?, ?, ?, ?);
        """, r)

    # 2. Seed Users with hashed passwords
    pw_hash_admin, salt_admin = hash_password("admin123")
    pw_hash_mgr, salt_mgr = hash_password("manager123")
    pw_hash_snr, salt_snr = hash_password("planner123")
    pw_hash_jnr, salt_jnr = hash_password("planner123")
    pw_hash_view, salt_view = hash_password("viewer123")

    users = [
        ("U-ADMIN-01", "System Administrator", "Admin", 1000.0, pw_hash_admin, salt_admin),
        ("U-MANAGER-01", "David Chen", "Supply Chain Manager", 100.0, pw_hash_mgr, salt_mgr),
        ("U-SENIOR-01", "Maria Garcia", "Senior Planner", 50.0, pw_hash_snr, salt_snr),
        ("U-JUNIOR-01", "Alex Smith", "Junior Planner", 20.0, pw_hash_jnr, salt_jnr),
        ("U-VIEWER-01", "Guest User", "Viewer", 0.0, pw_hash_view, salt_view)
    ]
    for u in users:
        cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, user_name, role, max_override_pct, password_hash, salt)
        VALUES (?, ?, ?, ?, ?, ?);
        """, u)

    # 3. Seed Master Override Reasons
    reasons = [
        ("R01", "Recent equipment failure", "Unscheduled equipment failure logged in field.", 1, "Emergency"),
        ("R02", "Customer emergency", "Critical customer emergency request.", 1, "Emergency"),
        ("R03", "Supplier delay", "Supplier lead-time delay requiring inventory buffer.", 1, "Supplier"),
        ("R04", "Historical forecast inaccurate", "Baseline model lagging behind actual demand pattern.", 1, "Forecast"),
        ("R05", "Seasonal demand", "Known seasonal surge not captured in moving average.", 1, "Demand"),
        ("R06", "Inventory concern", "Safety stock replenishment requirement.", 1, "Inventory"),
        ("R07", "Planned maintenance", "Scheduled preventive maintenance campaign.", 1, "Maintenance"),
        ("R08", "Data quality issue", "Known data pipeline error or duplicate record.", 1, "Data Quality"),
        ("R09", "Customer-specific requirement", "Special project or non-standard customer order.", 1, "Customer"),
        ("R10", "Other", "Other planner rationale.", 1, "General")
    ]
    for r in reasons:
        cursor.execute("""
        INSERT OR REPLACE INTO override_reasons (reason_code, reason_name, description, is_active, default_category)
        VALUES (?, ?, ?, ?, ?);
        """, r)

    # 4. Seed Suppliers
    suppliers = [
        ("SUP-101", "Apex Logistics & Hydraulics", 150, 45, 105, 5, 98.2, "North America"),
        ("SUP-102", "Titan Industrial Bearings", 120, 30, 90, 7, 94.5, "Europe"),
        ("SUP-103", "Precision Valve Global", 200, 60, 140, 4, 99.1, "Asia-Pacific"),
        ("SUP-104", "Vortex Power Systems", 100, 20, 80, 10, 91.0, "Latin America")
    ]
    for s in suppliers:
        cursor.execute("""
        INSERT OR REPLACE INTO suppliers (supplier_id, supplier_name, capacity, current_allocation, remaining_capacity, lead_time_days, reliability_score, location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, s)

    # 5. Seed Drivers (20 realistic drivers)
    drivers = []
    for i in range(1, 21):
        did = f"D{100 + i}"
        name = f"Driver {did}"
        max_safe = 50.0
        if i % 7 == 0:
            assigned = round(52.0 + (i * 0.5), 1)
        elif i % 3 == 0:
            assigned = round(42.0 + (i * 0.3), 1)
        else:
            assigned = round(25.0 + (i * 0.8), 1)

        avail = round(max(0, max_safe - assigned), 1)
        workload_pct = round((assigned / max_safe) * 100.0, 1)

        if workload_pct <= 80.0:
            status = "SAFE"
        elif workload_pct <= 100.0:
            status = "WARNING"
        else:
            status = "UNSAFE / REJECT"

        fatigue = round(min(100.0, workload_pct * 0.9), 1)
        drivers.append((did, name, avail, assigned, max_safe, workload_pct, status, fatigue))

    for d in drivers:
        cursor.execute("""
        INSERT OR REPLACE INTO drivers (driver_id, driver_name, available_hours, assigned_hours, maximum_safe_hours, workload_percentage, safety_status, fatigue_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, d)

    # 6. Seed System Settings
    settings = [
        ("junior_planner_limit_pct", "20.0"),
        ("senior_planner_limit_pct", "50.0"),
        ("manager_limit_pct", "100.0"),
        ("driver_max_safe_hours", "50.0"),
        ("active_forecasting_model", "Moving Average"),
        ("auto_approval_enabled", "True")
    ]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for s_key, s_val in settings:
        cursor.execute("""
        INSERT OR IGNORE INTO settings (setting_key, setting_value, updated_at, updated_by)
        VALUES (?, ?, ?, 'SYSTEM');
        """, (s_key, s_val, now_str))

    conn.commit()
    conn.close()

def populate_db_from_dataframe(df, db_path=None):
    """
    Populates SQLite database tables from raw synthetic pandas DataFrame.
    """
    init_db(db_path)
    seed_users_and_drivers(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Populate Parts
    parts_df = df[["Part_ID", "Part_Name", "Inventory_Level", "Safety_Stock", "Supplier_Capacity", "Lead_Time_Days"]].drop_duplicates(subset=["Part_ID"])
    for _, row in parts_df.iterrows():
        reorder_p = int(row["Safety_Stock"] + 10)
        cursor.execute("""
        INSERT OR REPLACE INTO parts (part_id, part_name, inventory_level, safety_stock, supplier_capacity, lead_time_days, reorder_point, supplier_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'SUP-101');
        """, (row["Part_ID"], row["Part_Name"], int(row["Inventory_Level"]), int(row["Safety_Stock"]), int(row["Supplier_Capacity"]), int(row["Lead_Time_Days"]), reorder_p))

    # Populate Equipment
    eq_df = df[["Equipment_ID", "Equipment_Type", "Customer_ID", "Region"]].drop_duplicates(subset=["Equipment_ID"])
    for _, row in eq_df.iterrows():
        cursor.execute("""
        INSERT OR REPLACE INTO equipment (equipment_id, equipment_type, customer_id, region, installation_year)
        VALUES (?, ?, ?, ?, 2021);
        """, (row["Equipment_ID"], row["Equipment_Type"], row["Customer_ID"], row["Region"]))

    # Populate Forecasts, Overrides, Constraints, Deliveries, Outcomes
    for _, row in df.iterrows():
        rec_id = row["Record_ID"]
        hist_d = int(row["Historical_Demand"])
        base_f = int(row["Baseline_Forecast"])
        act_d = int(row["Actual_Demand"])
        f_err = abs(base_f - act_d)
        adv_f = row.get("Advanced_Forecast", int(base_f * 0.95))

        cursor.execute("""
        INSERT OR REPLACE INTO forecasts (record_id, part_id, equipment_id, failure_date, failure_type, demand_pattern, historical_demand, baseline_forecast, advanced_forecast, actual_demand, forecast_error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (rec_id, row["Part_ID"], row["Equipment_ID"], row["Failure_Date"], row["Failure_Type"], row["Demand_Pattern"], hist_d, base_f, adv_f, act_d, f_err))

        planner_id = "U-SENIOR-01"
        planner_role = "Senior Planner"
        over_qty = int(row["Override_Quantity"])
        reason_c = row["Override_Reason"] if pd.notna(row["Override_Reason"]) else None
        reason_comm = row["Reason_Comment"] if pd.notna(row["Reason_Comment"]) else None
        final_d = int(row["Final_Demand"])

        direction = "INCREASE" if over_qty >= 0 else "DECREASE"
        pct_change = abs(over_qty / base_f * 100.0) if base_f > 0 else (100.0 if over_qty > 0 else 0.0)
        app_status = "APPROVED" if pct_change <= 50.0 else "PENDING APPROVAL"
        app_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO overrides (record_id, planner_id, planner_role, override_quantity, direction, override_pct, reason_code, reason_comment, final_demand, approval_status, approval_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (rec_id, planner_id, planner_role, over_qty, direction, pct_change, reason_c, reason_comm, final_d, app_status, app_time))
        override_id = cursor.lastrowid

        # Insert Approval Record
        cursor.execute("""
        INSERT INTO approvals (override_id, requested_by, approver_id, status, timestamp)
        VALUES (?, ?, ?, ?, ?);
        """, (override_id, planner_id, "U-MANAGER-01" if app_status == "APPROVED" else None, app_status, app_time))

        # Constraints
        supp_cap = int(row["Supplier_Capacity"])
        hard_status = "PASS"
        violation_details = ""
        if final_d < 0:
            hard_status = "REJECT"
            violation_details += "Invalid negative demand. "
        if final_d > supp_cap:
            hard_status = "REJECT"
            violation_details += f"Exceeds supplier capacity ({supp_cap}). "
        if row["Planner_Override"] == "YES" and not reason_c:
            hard_status = "REJECT"
            violation_details += "Missing override reason. "

        human_exp = violation_details if violation_details else "All hard constraints satisfied."
        cursor.execute("""
        INSERT INTO constraints (override_id, hard_status, soft_status, violation_details, human_explanation)
        VALUES (?, ?, ?, ?, ?);
        """, (override_id, hard_status, "PASS", violation_details, human_exp))

        # Delivery
        dist_km = float(row["Delivery_Distance_KM"]) if pd.notna(row["Delivery_Distance_KM"]) else 100.0
        cursor.execute("""
        INSERT INTO deliveries (record_id, driver_id, vehicle_type, delivery_distance_km, delivery_time_hours, estimated_cost, estimated_emissions)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (rec_id, row["Driver_ID"], row["Vehicle_Type"], dist_km, float(row["Delivery_Time_Hours"]), float(row["Estimated_Cost"]), float(row["Estimated_Emissions"])))

        # Outcome
        override_err = abs(final_d - act_d)
        improved = "YES" if override_err < f_err else "NO"
        err_imp = round(f_err - override_err, 2)
        cursor.execute("""
        INSERT INTO outcomes (record_id, baseline_error, override_error, override_improved, stockout_flag, emergency_order_flag, service_level, error_improvement)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (rec_id, f_err, override_err, improved, int(row["Stockout_Flag"]), int(row["Emergency_Order_Flag"]), float(row["Service_Level"]), err_imp))

    conn.commit()
    conn.close()
    print("Database schema migration & data loading completed successfully!")

if __name__ == "__main__":
    init_db()
    seed_users_and_drivers()
    print("Database initialization & seed complete!")
