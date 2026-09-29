"""
Unit tests for Data Ingestion and Validation Engine.
"""

import pytest
import pandas as pd
from src.ingestion import validate_dataframe

def test_validate_dataframe_valid():
    df = pd.DataFrame([{
        "Record_ID": "REC-001",
        "Part_ID": "P101",
        "Equipment_ID": "EQ-001",
        "Failure_Date": "2025-05-10",
        "Historical_Demand": 20,
        "Baseline_Forecast": 22,
        "Actual_Demand": 25,
        "Inventory_Level": 30,
        "Safety_Stock": 10,
        "Supplier_Capacity": 100,
        "Lead_Time_Days": 5
    }])

    df_clean, summary = validate_dataframe(df)
    assert summary["is_valid"] is True
    assert len(summary["errors"]) == 0

def test_validate_dataframe_missing_column():
    df = pd.DataFrame([{"Record_ID": "REC-001"}])
    df_clean, summary = validate_dataframe(df)
    assert summary["is_valid"] is False
    assert any("Missing required columns" in err for err in summary["errors"])

def test_validate_dataframe_negative_quantity():
    df = pd.DataFrame([{
        "Record_ID": "REC-001",
        "Part_ID": "P101",
        "Equipment_ID": "EQ-001",
        "Failure_Date": "2025-05-10",
        "Historical_Demand": -5,  # Invalid negative
        "Baseline_Forecast": 22,
        "Actual_Demand": 25,
        "Inventory_Level": 30,
        "Safety_Stock": 10,
        "Supplier_Capacity": 100,
        "Lead_Time_Days": 5
    }])

    df_clean, summary = validate_dataframe(df)
    assert summary["is_valid"] is False
    assert any("negative values" in err for err in summary["errors"])
