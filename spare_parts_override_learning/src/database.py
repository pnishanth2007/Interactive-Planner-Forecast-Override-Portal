"""
Database module for SQLite storage and retrieval.
Manages relational schema: users, parts, equipment, forecasts, overrides, constraints, drivers, deliveries, outcomes.
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime

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

def init_db(db_path=None):
    """
    Initializes SQLite tables with appropriate primary keys, foreign keys, and indexes.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
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

    # 2. Parts Table
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

    # 3. Equipment Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment (
        equipment_id TEXT PRIMARY KEY,
        equipment_type TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        region TEXT NOT NULL
    );
    """)

    # 4. Forecasts Table
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

    # 5. Overrides Table
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

    # 6. Constraints Table
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

    # 7. Drivers Table
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

    # 8. Deliveries Table
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

    # 9. Outcomes Table
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

    conn.commit()
    conn.close()

def seed_users_and_drivers(db_path=None):
    """
    Seeds default user profiles and drivers.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Seed Users
    users = [
        ("U-JUNIOR-01", "Alex Smith", "Junior Planner", 20.0),
        ("U-SENIOR-01", "Maria Garcia", "Senior Planner", 50.0),
        ("U-MANAGER-01", "David Chen", "Planning Manager", 100.0)
    ]
    cursor.executemany("""
    INSERT OR REPLACE INTO users (user_id, user_name, role, max_override_pct)
    VALUES (?, ?, ?, ?);
    """, users)

    # Seed 20 Drivers with realistic hours
    drivers = []
    for i in range(1, 21):
        did = f"D{100 + i}"
        name = f"Driver {did}"
        max_safe = 50.0  # Safe weekly drive hours
        # Generate varied assigned hours (some safe, some warning, some unsafe)
        if i % 7 == 0:
            assigned = round(52.0 + (i * 0.5), 1)  # Unsafe > 100%
        elif i % 3 == 0:
            assigned = round(42.0 + (i * 0.3), 1)  # Warning 80-100%
        else:
            assigned = round(25.0 + (i * 0.8), 1)  # Safe <= 80%

        avail = round(max(0, max_safe - assigned), 1)
        workload_pct = round((assigned / max_safe) * 100.0, 1)

        if workload_pct <= 80.0:
            status = "SAFE"
        elif workload_pct <= 100.0:
            status = "WARNING"
        else:
            status = "UNSAFE / REJECT"

        drivers.append((did, name, avail, assigned, max_safe, workload_pct, status))

    cursor.executemany("""
    INSERT OR REPLACE INTO drivers (driver_id, driver_name, available_hours, assigned_hours, maximum_safe_hours, workload_percentage, safety_status)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, drivers)

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

    # 1. Populate Parts
    parts_df = df[["Part_ID", "Part_Name", "Inventory_Level", "Safety_Stock", "Supplier_Capacity", "Lead_Time_Days"]].drop_duplicates(subset=["Part_ID"])
    for _, row in parts_df.iterrows():
        cursor.execute("""
        INSERT OR REPLACE INTO parts (part_id, part_name, inventory_level, safety_stock, supplier_capacity, lead_time_days)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (row["Part_ID"], row["Part_Name"], int(row["Inventory_Level"]), int(row["Safety_Stock"]), int(row["Supplier_Capacity"]), int(row["Lead_Time_Days"])))

    # 2. Populate Equipment
    eq_df = df[["Equipment_ID", "Equipment_Type", "Customer_ID", "Region"]].drop_duplicates(subset=["Equipment_ID"])
    for _, row in eq_df.iterrows():
        cursor.execute("""
        INSERT OR REPLACE INTO equipment (equipment_id, equipment_type, customer_id, region)
        VALUES (?, ?, ?, ?);
        """, (row["Equipment_ID"], row["Equipment_Type"], row["Customer_ID"], row["Region"]))

    # 3. Populate Forecasts, Overrides, Constraints, Deliveries, Outcomes
    for _, row in df.iterrows():
        rec_id = row["Record_ID"]
        hist_d = int(row["Historical_Demand"])
        base_f = int(row["Baseline_Forecast"])
        act_d = int(row["Actual_Demand"])
        f_err = abs(base_f - act_d)

        cursor.execute("""
        INSERT OR REPLACE INTO forecasts (record_id, part_id, equipment_id, failure_date, failure_type, demand_pattern, historical_demand, baseline_forecast, actual_demand, forecast_error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (rec_id, row["Part_ID"], row["Equipment_ID"], row["Failure_Date"], row["Failure_Type"], row["Demand_Pattern"], hist_d, base_f, act_d, f_err))

        # Override data
        planner_id = "U-SENIOR-01"
        planner_role = "Senior Planner"
        over_qty = int(row["Override_Quantity"])
        reason_c = row["Override_Reason"] if pd.notna(row["Override_Reason"]) else None
        reason_comm = row["Reason_Comment"] if pd.notna(row["Reason_Comment"]) else None
        final_d = int(row["Final_Demand"])

        # Determine authorization status
        pct_change = abs(over_qty / base_f * 100.0) if base_f > 0 else (100.0 if over_qty > 0 else 0.0)
        app_status = "APPROVED" if pct_change <= 50.0 else "PENDING APPROVAL"
        app_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO overrides (record_id, planner_id, planner_role, override_quantity, reason_code, reason_comment, final_demand, approval_status, approval_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (rec_id, planner_id, planner_role, over_qty, reason_c, reason_comm, final_d, app_status, app_time))
        override_id = cursor.lastrowid

        # Constraint check
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
        if hard_status == "PASS":
            violation_details = "All hard constraints satisfied."

        cursor.execute("""
        INSERT INTO constraints (override_id, hard_status, soft_status, violation_details)
        VALUES (?, ?, ?, ?);
        """, (override_id, hard_status, "PASS", violation_details))

        # Delivery
        dist_km = float(row["Delivery_Distance_KM"]) if pd.notna(row["Delivery_Distance_KM"]) else 100.0
        cursor.execute("""
        INSERT INTO deliveries (record_id, driver_id, vehicle_type, delivery_distance_km, delivery_time_hours, estimated_cost, estimated_emissions)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (rec_id, row["Driver_ID"], row["Vehicle_Type"], dist_km, float(row["Delivery_Time_Hours"]), float(row["Estimated_Cost"]), float(row["Estimated_Emissions"])))

        # Outcome
        override_err = abs(final_d - act_d)
        improved = "YES" if override_err < f_err else "NO"
        cursor.execute("""
        INSERT INTO outcomes (record_id, baseline_error, override_error, override_improved, stockout_flag, emergency_order_flag, service_level)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (rec_id, f_err, override_err, improved, int(row["Stockout_Flag"]), int(row["Emergency_Order_Flag"]), float(row["Service_Level"])))

    conn.commit()
    conn.close()
    print("Database population from DataFrame completed successfully!")

if __name__ == "__main__":
    init_db()
    seed_users_and_drivers()
    print("Database schema initialized!")
