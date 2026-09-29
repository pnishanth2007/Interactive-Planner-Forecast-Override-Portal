"""
API-Ready Connector Adapters & GPS Telemetry Stream Simulator.
Provides mock connector interfaces for SAP, Oracle ERP, WMS, GPS Telemetry, and Supplier EDI APIs.
Enables instant plug-and-play connection to real enterprise APIs in future releases.
"""

import random
from datetime import datetime

class ERPConnector:
    """Mock adapter for SAP / Oracle ERP systems."""
    def __init__(self, endpoint_url: str = "https://api.erp.internal/v1"):
        self.endpoint_url = endpoint_url
        self.is_connected = False

    def connect(self) -> bool:
        self.is_connected = True
        return True

    def fetch_demand_history(self, part_id: str) -> list[dict]:
        """Simulates fetching historical consumption from SAP MM module."""
        return [
            {"date": f"2025-{m:02d}-01", "quantity": random.randint(10, 50)}
            for m in range(1, 13)
        ]

class WMSConnector:
    """Mock adapter for Warehouse Management System (WMS)."""
    def __init__(self, warehouse_code: str = "WH-CENTRAL-01"):
        self.warehouse_code = warehouse_code

    def check_bin_stock(self, part_id: str) -> dict:
        """Simulates querying real-time physical bin location stock."""
        return {
            "part_id": part_id,
            "warehouse": self.warehouse_code,
            "on_hand": random.randint(20, 80),
            "allocated": random.randint(5, 15),
            "available": random.randint(15, 65)
        }

class GPSConnector:
    """Mock adapter for real-time GPS telemetry stream."""
    def __init__(self, fleet_id: str = "FLEET-NORTH-01"):
        self.fleet_id = fleet_id

    def stream_driver_telemetry(self, driver_id: str) -> dict:
        """
        Simulates live GPS telemetry ping from vehicle OBD-II tracking device.
        """
        base_lat = 40.7128 + random.uniform(-0.5, 0.5)
        base_lon = -74.0060 + random.uniform(-0.5, 0.5)
        speed = round(random.uniform(40.0, 85.0), 1)
        driving_hours = round(random.uniform(2.5, 9.0), 1)
        traffic = random.choice(["Low", "Moderate", "Heavy", "Severe Congestion"])
        status = "NORMAL" if driving_hours <= 8.0 else "FATIGUE_WARNING"

        return {
            "driver_id": driver_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": round(base_lat, 6),
            "longitude": round(base_lon, 6),
            "speed_kmh": speed,
            "driving_hours": driving_hours,
            "traffic_condition": traffic,
            "status_flag": status,
            "is_simulated": True
        }

class SupplierConnector:
    """Mock adapter for Supplier EDI Capacity Query APIs."""
    def __init__(self, edi_partner_id: str = "EDI-SUP-APEX"):
        self.partner_id = edi_partner_id

    def query_capacity(self, supplier_id: str, part_id: str) -> dict:
        """Simulates querying supplier's current monthly production capacity via EDI 830."""
        return {
            "supplier_id": supplier_id,
            "part_id": part_id,
            "available_capacity": random.randint(50, 200),
            "committed_orders": random.randint(20, 80),
            "lead_time_days": random.randint(3, 10),
            "edi_status": "ACKNOWLEDGED"
        }
