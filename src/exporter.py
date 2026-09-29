"""
Data Export Module.
Generates downloadable CSV and Excel files for forecasts, overrides, inventory recommendations,
supplier intelligence, audit logs, and model performance reports.
"""

import os
import io
import pandas as pd

def generate_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Converts a pandas DataFrame to CSV bytes for web download.
    """
    return df.to_csv(index=False).encode('utf-8')

def generate_excel_bytes(df: pd.DataFrame, sheet_name: str = "Report") -> bytes:
    """
    Converts a pandas DataFrame to Excel (.xlsx) bytes using openpyxl.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()

def export_report_to_disk(df: pd.DataFrame, filename: str, format_type: str = "csv", base_dir: str = None) -> str:
    """
    Saves export report directly to data/exports/ folder.
    Returns absolute file path.
    """
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    export_dir = os.path.join(base_dir, "data", "exports")
    os.makedirs(export_dir, exist_ok=True)

    if not filename.endswith(f".{format_type}"):
        filename = f"{filename}.{format_type}"

    file_path = os.path.join(export_dir, filename)

    if format_type.lower() == "xlsx" or format_type.lower() == "excel":
        df.to_excel(file_path, index=False, engine='openpyxl')
    else:
        df.to_csv(file_path, index=False)

    return file_path
