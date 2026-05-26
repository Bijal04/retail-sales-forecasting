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


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    print(f"  Duplicates removed: {before - len(df):,}")
    return df


def flag_cancellations(df: pd.DataFrame):
    df["IsCancelled"] = df["Invoice"].str.startswith("C")
    df_cancelled = df[df["IsCancelled"]].copy()
    df_sales     = df[~df["IsCancelled"]].copy()
    print(f"  Cancellations: {len(df_cancelled):,}  |  Valid sales: {len(df_sales):,}")
    return df_sales, df_cancelled


def remove_invalid_values(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df[(df["Quantity"] > 0) & (df["Price"] > 0)]
    print(f"  Invalid Qty/Price removed: {before - len(df):,}")
    return df


def fill_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    desc_map = (
        df[df["Description"].notna()]
        .groupby("StockCode")["Description"]
        .agg(lambda x: x.mode()[0] if len(x) > 0 else "Unknown")
    )
    mask = df["Description"].isna() | (df["Description"] == "Nan")
    df.loc[mask, "Description"] = df.loc[mask, "StockCode"].map(desc_map)
    df["Description"] = df["Description"].fillna("Unknown")
    return df


def remove_noise_codes(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df[~df["StockCode"].isin(NOISE_CODES)]
    df = df[df["StockCode"].str.len() >= 4]
    print(f"  Noise codes removed: {before - len(df):,}")
    return df

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df["HasCustomerID"]   = df["CustomerID"].notna()
    df["TotalRevenue"]    = (df["Quantity"] * df["Price"]).round(2)
    df["Year"]            = df["InvoiceDate"].dt.year
    df["Month"]           = df["InvoiceDate"].dt.month
    df["YearMonth"]       = df["InvoiceDate"].dt.to_period("M").astype(str)
    df["DayOfWeek"]       = df["InvoiceDate"].dt.dayofweek
    df["DayOfWeekName"]   = df["InvoiceDate"].dt.day_name()
    df["Hour"]            = df["InvoiceDate"].dt.hour
    df["Quarter"]         = df["InvoiceDate"].dt.quarter
    df["WeekOfYear"]      = df["InvoiceDate"].dt.isocalendar().week.astype(int)
    return df

def save_outputs(df_sales: pd.DataFrame, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)

    df_sales.to_csv(f"{out_dir}/cleaned_sales.csv", index=False)

    monthly = (
        df_sales.groupby("YearMonth")
        .agg(
            TotalRevenue  = ("TotalRevenue", "sum"),
            TotalQuantity = ("Quantity",     "sum"),
            NumInvoices   = ("Invoice",      "nunique"),
            NumCustomers  = ("CustomerID",   "nunique"),
            NumProducts   = ("StockCode",    "nunique"),
        )
        .reset_index()
        .sort_values("YearMonth")
    )
    monthly.to_csv(f"{out_dir}/monthly_sales.csv", index=False)

    monthly_cat = (
        df_sales.groupby(["YearMonth", "StockCode", "Description"])
        .agg(Revenue=("TotalRevenue", "sum"), Qty=("Quantity", "sum"))
        .reset_index()
        .sort_values(["StockCode", "YearMonth"])
    )
    monthly_cat.to_csv(f"{out_dir}/monthly_by_product.csv", index=False)

    print(f"\nSaved to {out_dir}/:")
    print(f"  cleaned_sales.csv       — {len(df_sales):,} rows")
    print(f"  monthly_sales.csv       — {len(monthly)} months")
    print(f"  monthly_by_product.csv  — {len(monthly_cat):,} rows")


def print_summary(df: pd.DataFrame) -> None:
    print("\n=== FINAL SUMMARY ===")
    print(f"Rows       : {len(df):,}")
    print(f"Date range : {df['InvoiceDate'].min().date()} → {df['InvoiceDate'].max().date()}")
    print(f"Customers  : {df['CustomerID'].nunique():,}")
    print(f"Products   : {df['StockCode'].nunique():,}")
    print(f"Countries  : {df['Country'].nunique()}")
    print(f"Revenue    : £{df['TotalRevenue'].sum():,.2f}")
    nulls = df.isnull().sum()
    if nulls.any():
        print("\nRemaining nulls:")
        print(nulls[nulls > 0])


def main():
    print("=== DATA CLEANING PIPELINE ===\n")

    df = load_and_merge(RAW_PATH)
    df = fix_dtypes(df)
    df = remove_duplicates(df)
    df, _ = flag_cancellations(df)
    df = remove_invalid_values(df)
    df = fill_descriptions(df)
    df = remove_noise_codes(df)
    df = add_features(df)

    print_summary(df)
    save_outputs(df, PROCESSED_DIR)

    print("\n✓ Done. Next: notebooks/02_eda.ipynb")


if __name__ == "__main__":
    main()

