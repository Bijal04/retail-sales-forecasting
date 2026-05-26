"""
data_cleaning.py
~~~~~~~~~~~~~~~~
Standalone script version of notebooks/01_data_cleaning.ipynb.
Run:  python src/data_cleaning.py
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

RAW_PATH       = "data/raw/online_retail_II.xlsx"
PROCESSED_DIR  = "data/processed"

NOISE_CODES = {
    "POST", "D", "DOT", "M", "BANK CHARGES",
    "PADS", "AMAZONFEE", "C2", "CRUK"
}


def load_and_merge(path: str) -> pd.DataFrame:
    print("Loading Year 2009-2010 ...")
    df1 = pd.read_excel(path, sheet_name="Year 2009-2010")
    print("Loading Year 2010-2011 ...")
    df2 = pd.read_excel(path, sheet_name="Year 2010-2011")
    df  = pd.concat([df1, df2], ignore_index=True)
    print(f"  Merged: {len(df):,} rows  |  {df.shape[1]} columns")
    return df

def fix_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [
        "Invoice", "StockCode", "Description", "Quantity",
        "InvoiceDate", "Price", "CustomerID", "Country"
    ]
    df["Invoice"]     = df["Invoice"].astype(str).str.strip()
    df["StockCode"]   = df["StockCode"].astype(str).str.strip().str.upper()
    df["Description"] = df["Description"].astype(str).str.strip().str.title()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["CustomerID"]  = df["CustomerID"].astype("Int64")
    df["Country"]     = df["Country"].astype(str).str.strip()
    return df

