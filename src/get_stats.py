import pandas as pd
import sqlite3

# CSV stats
df = pd.read_csv('data/processed/cleaned_sales.csv')
monthly = pd.read_csv('data/processed/monthly_sales.csv')
rfm = pd.read_csv('data/processed/rfm_segments.csv')
forecast = pd.read_csv('data/processed/revenue_forecast.csv')
model = pd.read_csv('data/processed/model_summary.csv')

print("=== YOUR REAL NUMBERS ===")
print(f"Total rows:        {len(df):,}")
print(f"Unique customers:  {df['CustomerID'].nunique():,}")
print(f"Unique products:   {df['StockCode'].nunique():,}")
print(f"Unique countries:  {df['Country'].nunique():,}")
print(f"Date range:        {df['InvoiceDate'].min()} → {df['InvoiceDate'].max()}")
print(f"Monthly periods:   {len(monthly)}")
print(f"Forecast months:   {len(forecast)}")
print(f"RFM customers:     {len(rfm):,}")
print(f"RFM segments:      {rfm['segment'].nunique()}")
print(f"Champions:         {len(rfm[rfm['segment']=='Champions']):,}")
print(f"At Risk:           {len(rfm[rfm['segment']=='At Risk']):,}")

# Model accuracy
print(f"\n=== MODEL PERFORMANCE ===")
print(model.to_string(index=False))

# DB stats
conn = sqlite3.connect('retail_dw.db')
tables = ['fact_sales','dim_date','dim_product','dim_customer','dim_country']
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t}: {count:,} rows")
conn.close()