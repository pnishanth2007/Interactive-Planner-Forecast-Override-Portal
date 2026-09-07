"""
Preprocessing Module.
Handles data cleaning, missing value imputation, feature encoding, and data transformation for forecasting models.
"""

import pandas as pd
import numpy as np

def clean_data(df):
    """
    Cleans raw spare-parts dataset: imputes missing values and enforces proper data types.
    """
    df_clean = df.copy()

    # Impute missing Reason_Comment with default string
    if "Reason_Comment" in df_clean.columns:
        df_clean["Reason_Comment"] = df_clean["Reason_Comment"].fillna("No comment provided")

    # Impute missing Delivery_Distance_KM with median distance
    if "Delivery_Distance_KM" in df_clean.columns:
        median_dist = df_clean["Delivery_Distance_KM"].median()
        df_clean["Delivery_Distance_KM"] = df_clean["Delivery_Distance_KM"].fillna(median_dist)

    # Ensure numeric types
    numeric_cols = [
        "Historical_Demand", "Baseline_Forecast", "Inventory_Level",
        "Safety_Stock", "Supplier_Capacity", "Lead_Time_Days",
        "Delivery_Distance_KM", "Actual_Demand", "Override_Quantity",
        "Final_Demand", "Estimated_Cost", "Estimated_Emissions",
        "Delivery_Time_Hours", "Service_Level", "Stockout_Flag", "Emergency_Order_Flag"
    ]

    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)

    # Ensure Date format
    if "Failure_Date" in df_clean.columns:
        df_clean["Failure_Date"] = pd.to_datetime(df_clean["Failure_Date"], errors="coerce")

    return df_clean

def prepare_forecasting_features(df):
    """
    Prepares feature set for machine learning baseline forecasting models.
    """
    df_clean = clean_data(df)

    # One-hot encoding for categorical variables
    cat_cols = ["Part_ID", "Equipment_Type", "Region", "Failure_Type", "Demand_Pattern"]
    features = pd.get_dummies(df_clean[cat_cols], drop_first=True)

    # Add numeric features
    numeric_feats = ["Historical_Demand", "Inventory_Level", "Safety_Stock", "Lead_Time_Days"]
    X = pd.concat([features, df_clean[numeric_feats]], axis=1)
    y = df_clean["Actual_Demand"]

    return X, y
