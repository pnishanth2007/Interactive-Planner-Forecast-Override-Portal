"""
Synthetic Data Generator for Spare-Parts Demand Planning.
Generates 10,000+ realistic records with irregular failure patterns, planner overrides, and logistical constraints.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_spare_parts_data(num_records=10000, random_seed=42):
    """
    Generates a realistic synthetic spare-parts dataset containing irregular equipment failures,
    planner overrides, constraints, and demand outcomes.
    """
    np.random.seed(random_seed)
    random.seed(random_seed)

    parts = [
        ("P101", "Hydraulic Cylinder Seal Kit", "Hydraulics", 120.0, "SUP-101"),
        ("P102", "High-Pressure Oil Pump", "Pumps", 450.0, "SUP-101"),
        ("P103", "Turbine Bearing Assembly", "Turbines", 850.0, "SUP-102"),
        ("P104", "Control Valve Solenoid", "Valves", 210.0, "SUP-103"),
        ("P105", "Cooling System Thermostat", "Cooling", 95.0, "SUP-101"),
        ("P106", "Transmission Gear Module", "Transmission", 620.0, "SUP-102"),
        ("P107", "Heavy Duty Brake Disc", "Braking", 310.0, "SUP-104"),
        ("P108", "Electronic Control Unit (ECU)", "Electronics", 980.0, "SUP-103"),
        ("P109", "Pneumatic Pressure Sensor", "Sensors", 175.0, "SUP-103"),
        ("P110", "Exhaust Gas Recirculation Valve", "Exhaust", 280.0, "SUP-104")
    ]

    equipment_types = [
        "Heavy Excavator EX-900",
        "Industrial Turbine GT-4000",
        "Mining Haul Truck HT-50",
        "Offshore Drilling Rig DR-10",
        "Hydraulic Press HP-250"
    ]

    regions = ["North America", "Europe", "Asia-Pacific", "Latin America", "Middle East & Africa"]
    failure_types = ["Wear and Tear", "Thermal Overload", "Electrical Short", "Hydraulic Contamination", "Structural Fatigue", "Unscheduled Maintenance"]
    severities = ["Low", "Moderate", "High", "Critical"]
    
    demand_patterns = [
        "Normal demand",
        "Intermittent demand",
        "Sudden spike",
        "Zero demand",
        "Seasonal demand",
        "Equipment failure cluster",
        "Emergency demand",
        "Unexpected failure"
    ]

    override_reasons = ["R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10"]
    vehicle_types = ["Standard Van", "Heavy Haul Truck", "Air Freight Transport", "Express Freighter"]
    driver_ids = [f"D{101 + i}" for i in range(20)]
    traffic_levels = ["Low", "Moderate", "Heavy", "Severe Congestion"]

    start_date = datetime(2025, 1, 1)
    records = []

    for i in range(1, num_records + 1):
        record_id = f"REC-{i:06d}"
        part_id, part_name, category, unit_cost, supplier_id = random.choice(parts)
        eq_type = random.choice(equipment_types)
        eq_id = f"EQ-{hash(eq_type + str(i % 150)) % 1000:04d}"
        customer_id = f"CUST-{random.randint(1001, 1200)}"
        region = random.choice(regions)

        days_offset = random.randint(0, 365)
        failure_date = (start_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        failure_type = random.choice(failure_types)
        severity = random.choice(severities)
        pattern = random.choice(demand_patterns)

        # Generate realistic demand according to pattern
        if pattern == "Zero demand":
            hist_demand = 0
            actual_demand = random.choices([0, 1], weights=[0.85, 0.15])[0]
        elif pattern == "Intermittent demand":
            hist_demand = random.choices([0, 1, 2, 5], weights=[0.6, 0.25, 0.1, 0.05])[0]
            actual_demand = random.choices([0, 1, 3, 6], weights=[0.55, 0.25, 0.12, 0.08])[0]
        elif pattern == "Sudden spike":
            hist_demand = random.randint(5, 15)
            actual_demand = random.randint(45, 120)
        elif pattern == "Equipment failure cluster":
            hist_demand = random.randint(10, 25)
            actual_demand = random.randint(35, 90)
        elif pattern == "Emergency demand":
            hist_demand = random.randint(2, 10)
            actual_demand = random.randint(30, 80)
        elif pattern == "Seasonal demand":
            month = (start_date + timedelta(days=days_offset)).month
            seasonal_mult = 2.2 if month in [6, 7, 8, 11, 12] else 0.8
            hist_demand = int(random.randint(10, 30) * seasonal_mult)
            actual_demand = int(hist_demand * np.random.uniform(0.9, 1.2))
        elif pattern == "Unexpected failure":
            hist_demand = random.randint(1, 5)
            actual_demand = random.randint(20, 60)
        else:  # Normal demand
            hist_demand = random.randint(15, 45)
            actual_demand = int(hist_demand * np.random.uniform(0.85, 1.15))

        # Baseline & Advanced Forecasts
        baseline_forecast = max(0, int(hist_demand * np.random.uniform(0.85, 1.15)))
        advanced_forecast = max(0, int(actual_demand * np.random.uniform(0.90, 1.08)))

        inventory_level = random.randint(5, 100)
        safety_stock = random.randint(5, 25)
        supplier_capacity = random.randint(30, 150)
        lead_time_days = random.randint(1, 14)
        delivery_dist_km = random.randint(15, 850)
        vehicle = random.choice(vehicle_types)
        driver_id = random.choice(driver_ids)
        traffic = random.choice(traffic_levels)

        planner_override_flag = random.choices(["YES", "NO"], weights=[0.80, 0.20])[0]

        if planner_override_flag == "YES":
            reason_code = random.choice(override_reasons)
            if reason_code in ["R01", "R02", "R07"]:
                diff = actual_demand - baseline_forecast
                override_qty = int(diff * np.random.uniform(0.7, 1.1)) if diff != 0 else random.randint(-2, 5)
            elif reason_code in ["R03", "R05", "R09"]:
                override_qty = random.randint(-10, 35)
            else:
                override_qty = random.randint(-15, 40)

            reason_comment = f"Planner adjustment based on {reason_code} for {eq_type}."
        else:
            reason_code = None
            override_qty = 0
            reason_comment = None

        final_demand = max(0, baseline_forecast + override_qty)

        estimated_cost = round(max(50.0, final_demand * unit_cost * 0.15 + delivery_dist_km * 0.8), 2)
        estimated_emissions = round(delivery_dist_km * random.uniform(0.15, 0.45) + final_demand * 0.05, 2)
        delivery_time_hours = round(delivery_dist_km / random.uniform(40.0, 70.0) + lead_time_days * 24, 1)

        stockout_flag = 1 if actual_demand > inventory_level else 0
        backorder_qty = max(0, actual_demand - inventory_level)
        emergency_order_flag = 1 if (stockout_flag == 1 or pattern in ["Emergency demand", "Sudden spike"] or reason_code == "R02") else 0
        
        if actual_demand > 0:
            fulfilled = min(actual_demand, max(0, final_demand))
            service_level = round(min(100.0, (fulfilled / actual_demand) * 100.0), 1)
        else:
            service_level = 100.0

        driver_hours = round(random.uniform(20.0, 58.0), 1)
        fatigue_risk = round(min(100.0, (driver_hours / 50.0) * 100.0), 1)

        records.append({
            "Record_ID": record_id,
            "Part_ID": part_id,
            "Part_Name": part_name,
            "Category": category,
            "Unit_Cost": unit_cost,
            "Supplier_ID": supplier_id,
            "Equipment_ID": eq_id,
            "Equipment_Type": eq_type,
            "Customer_ID": customer_id,
            "Region": region,
            "Failure_Date": failure_date,
            "Failure_Type": failure_type,
            "Failure_Severity": severity,
            "Demand_Pattern": pattern,
            "Historical_Demand": hist_demand,
            "Baseline_Forecast": baseline_forecast,
            "Advanced_Forecast": advanced_forecast,
            "Inventory_Level": inventory_level,
            "Safety_Stock": safety_stock,
            "Backorder_Quantity": backorder_qty,
            "Supplier_Capacity": supplier_capacity,
            "Lead_Time_Days": lead_time_days,
            "Delivery_Distance_KM": delivery_dist_km,
            "Vehicle_Type": vehicle,
            "Driver_ID": driver_id,
            "Driver_Hours": driver_hours,
            "Traffic_Level": traffic,
            "Fatigue_Risk": fatigue_risk,
            "Actual_Demand": actual_demand,
            "Planner_Override": planner_override_flag,
            "Override_Quantity": override_qty,
            "Override_Reason": reason_code,
            "Reason_Comment": reason_comment,
            "Final_Demand": final_demand,
            "Estimated_Cost": estimated_cost,
            "Estimated_Emissions": estimated_emissions,
            "Delivery_Time_Hours": delivery_time_hours,
            "Service_Level": service_level,
            "Stockout_Flag": stockout_flag,
            "Emergency_Order_Flag": emergency_order_flag
        })

    df = pd.DataFrame(records)
    return df

def generate_and_save_data(base_dir=None):
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    raw_dir = os.path.join(base_dir, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)

    csv_path = os.path.join(raw_dir, "spare_parts_data.csv")
    xlsx_path = os.path.join(raw_dir, "spare_parts_data.xlsx")

    print("Generating synthetic dataset with 10,000 records...")
    df = generate_spare_parts_data(num_records=10000)

    print(f"Saving dataset to CSV: {csv_path}")
    df.to_csv(csv_path, index=False)

    print(f"Saving dataset to Excel: {xlsx_path}")
    df.to_excel(xlsx_path, index=False, engine='openpyxl')

    print("Data generation complete!")
    return df

if __name__ == "__main__":
    generate_and_save_data()
