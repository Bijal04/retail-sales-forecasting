"""
Merge Two Sheets from Excel File
Combines 'Sheet1' and 'Sheet2' into one dataset.
"""

import pandas as pd
import os

# --- Configuration ---
EXCEL_PATH = r'C:\Users\bjpan\OneDrive\Documents\retail-sales-forecasting\data\raw\online_retail_II.xlsx'  # Your Excel file
OUTPUT_PATH = r'data\raw\merged_online_retail_II.csv'  # Save as CSV for easy use
SHEET_NAME_1 = 'Year 2009-2010'  # Change to your actual sheet name
SHEET_NAME_2 = 'Year 2010-2011'  # Change to your actual sheet name

def merge_excel_sheets(excel_path, sheet1, sheet2, output_path):
    """
    Reads two sheets and merges them vertically (concatenates).
    """
    print(f"Reading Excel file: {excel_path}")
    
    try:
        # Read both sheets
        df1 = pd.read_excel(excel_path, sheet_name=sheet1)
        print(f"Loaded '{sheet1}': {df1.shape[0]} rows")
        
        df2 = pd.read_excel(excel_path, sheet_name=sheet2)
        print(f"Loaded '{sheet2}': {df2.shape[0]} rows")
        
        # Check if columns are the same
        if list(df1.columns) != list(df2.columns):
            print("Warning: Column names differ between sheets!")
            print(f"Year 2009-2010 columns: {list(df1.columns)}")
            print(f"Year 2010-2011 columns: {list(df2.columns)}")
        
        # Merge (Concatenate) them
        df_combined = pd.concat([df1, df2], ignore_index=True)
        print(f"\n Merged Data: {df_combined.shape[0]} total rows")
        
        # Save to CSV
        df_combined.to_csv(output_path, index=False)
        print(f"Saved merged data to: {output_path}")
        
        return df_combined
        
    except Exception as e:
        print(f"Error: {e}")
        raise

# --- Main Execution ---
if __name__ == "__main__":
    # Check if file exists
    if os.path.exists(EXCEL_PATH):
        df = merge_excel_sheets(EXCEL_PATH, SHEET_NAME_1, SHEET_NAME_2, OUTPUT_PATH)
        print("\nProcess Completed!")
    else:
        print(f"File not found: {EXCEL_PATH}")
        print("Please place your Excel file in: ../data/raw/")