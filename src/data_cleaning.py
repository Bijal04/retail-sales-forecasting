import pandas as pd
import numpy as np
import os
import logging

#setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s -%(message)s')

def load_data(filepath):
    try:
        df = pd.read_csv(filepath, encoding='latin-1')
        logging.info(f"Data loaded successfully. Shape:{df.shape}")
        return df
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        raise

def clean_data(df):
    """cleans the retails II data:
    1. Convert date types
    2. Removes cancelled orders (InvoiceNo starting with 'C')
    3. Removes rows with missing CustomerID
    4. Removes nagative quantities
    5. Handle outliers
    """
    #1. Conver InvoiceDate to datetime
    df['InvoiceDate'] = pd.to_datetime(df['Invoicedate'])

    #2