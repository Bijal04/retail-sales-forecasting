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

