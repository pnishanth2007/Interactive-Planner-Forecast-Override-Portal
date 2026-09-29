"""
Data Ingestion & Validation Engine.
Handles CSV/Excel file uploads, schema validation, data quality checks, error reporting, and export management.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

REQUIRED_COLUMNS = [
    "Record_ID", "Part_ID", "Equipment_ID", "Failure_Date",
    "Historical_Demand", "Baseline_Forecast", "Actual_Demand",
    "Inventory_Level", "Safety_Stock", "Supplier_Capacity", "Lead_Time_Days"
]

def validate_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Validates uploaded DataFrame against spare-parts demand planning rules.
    Returns (cleaned_df, validation_summary).
    """
    errors = []
    warnings = []
    df_clean = df.copy()

    # 1. Missing Column Check
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df_clean.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return df_clean, {
            "is_valid": False,
            "errors": errors,
            "warnings": warnings,
            "rows_total": len(df_clean),
            "rows_valid": 0,
            "rows_invalid": len(df_clean)
        }

    total_rows = len(df_clean)

    # 2. Duplicate Record Check
    dups = df_clean.duplicated(subset=["Record_ID"]).sum()
    if dups > 0:
        warnings.append(f"Found {dups} duplicate Record_ID entries. Automatically deduping.")
        df_clean = df_clean.drop_duplicates(subset=["Record_ID"])

    # 3. Date Validation
    invalid_dates = pd.to_datetime(df_clean["Failure_Date"], errors="coerce").isna().sum()
    if invalid_dates > 0:
        warnings.append(f"Found {invalid_dates} invalid or missing Failure_Date entries.")

    # 4. Negative Quantity Check
    num_cols = ["Historical_Demand", "Baseline_Forecast", "Actual_Demand", "Inventory_Level", "Supplier_Capacity"]
    for c in num_cols:
        neg_count = (df_clean[c] < 0).sum()
        if neg_count > 0:
            errors.append(f"Column '{c}' contains {neg_count} negative values. Negative quantities are invalid.")

    # 5. Lead Time & Capacity Sanity Check
    bad_lead = (df_clean["Lead_Time_Days"] <= 0).sum()
    if bad_lead > 0:
        warnings.append(f"Found {bad_lead} records with non-positive Lead_Time_Days.")

    bad_cap = (df_clean["Supplier_Capacity"] <= 0).sum()
    if bad_cap > 0:
        warnings.append(f"Found {bad_cap} records with zero or negative Supplier_Capacity.")

    is_valid = len(errors) == 0
    valid_rows = len(df_clean) if is_valid else 0
    invalid_rows = total_rows - valid_rows

    summary = {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "rows_total": total_rows,
        "rows_valid": valid_rows,
        "rows_invalid": invalid_rows
    }

    return df_clean, summary

def process_file_upload(file_obj, base_dir=None) -> tuple[pd.DataFrame | None, dict]:
    """
    Ingests and validates a user-uploaded file (CSV or Excel).
    Saves raw file to `data/uploads/` directory.
    """
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    upload_dir = os.path.join(base_dir, "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    filename = getattr(file_obj, "name", f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    file_path = os.path.join(upload_dir, filename)

    try:
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(file_obj)
        else:
            df = pd.read_csv(file_obj)

        df_clean, summary = validate_dataframe(df)

        if summary["is_valid"]:
            if hasattr(file_obj, "getbuffer"):
                with open(file_path, "wb") as f:
                    f.write(file_obj.getbuffer())
            else:
                df.to_csv(file_path, index=False)

        return df_clean, summary
    except Exception as e:
        return None, {
            "is_valid": False,
            "errors": [f"File parsing error: {str(e)}"],
            "warnings": [],
            "rows_total": 0,
            "rows_valid": 0,
            "rows_invalid": 0
        }
