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
