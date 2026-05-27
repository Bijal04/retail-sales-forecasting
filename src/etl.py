"""
etl.py
~~~~~~
Loads cleaned_sales.csv into a local SQLite database
using the star schema defined in sql/schema.sql.

Run:  python src/etl.py

Output: retail_dw.db  (SQLite — open in DBeaver, DB Browser, or Power BI)

For PostgreSQL, change DB_URL and swap the COPY statements
with pd.to_sql() or psycopg2 bulk inserts.
"""

import pandas as pd
import numpy as np
import sqlite3
import os
import warnings
warnings.filterwarnings("ignore")

PROCESSED_DIR = "data/processed"
DB_PATH       = "retail_dw.db"


# ── Connect ───────────────────────────────────────────────────

def get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Create tables ─────────────────────────────────────────────

DDL = """
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_country;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS forecast_results;
DROP TABLE IF EXISTS inventory_risk;

CREATE TABLE dim_date (
    date_key      INTEGER PRIMARY KEY,
    full_date     TEXT,
    year          INTEGER,
    quarter       INTEGER,
    month         INTEGER,
    month_name    TEXT,
    week_of_year  INTEGER,
    day_of_month  INTEGER,
    day_of_week   INTEGER,
    day_name      TEXT,
    hour          INTEGER,
    year_month    TEXT,
    is_weekend    INTEGER DEFAULT 0
);

CREATE TABLE dim_product (
    product_key   INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code    TEXT NOT NULL UNIQUE,
    description   TEXT NOT NULL DEFAULT 'Unknown'
);

CREATE TABLE dim_customer (
    customer_key  INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL UNIQUE,
    has_account   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE dim_country (
    country_key   INTEGER PRIMARY KEY AUTOINCREMENT,
    country_name  TEXT NOT NULL UNIQUE,
    region        TEXT NOT NULL DEFAULT 'Other'
);

CREATE TABLE fact_sales (
    sale_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no    TEXT    NOT NULL,
    date_key      INTEGER NOT NULL REFERENCES dim_date(date_key),
    product_key   INTEGER NOT NULL REFERENCES dim_product(product_key),
    customer_key  INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    country_key   INTEGER NOT NULL REFERENCES dim_country(country_key),
    quantity      INTEGER NOT NULL,
    unit_price    REAL    NOT NULL,
    total_revenue REAL    NOT NULL
);

CREATE TABLE forecast_results (
    forecast_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    year_month       TEXT    NOT NULL UNIQUE,
    forecast_revenue REAL    NOT NULL,
    lower_80ci       REAL,
    upper_80ci       REAL,
    model_used       TEXT,
    generated_at     TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE inventory_risk (
    risk_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code       TEXT,
    description      TEXT,
    avg_monthly_qty  INTEGER,
    stockout_flag    INTEGER DEFAULT 0,
    risk_level       TEXT,
    updated_at       TEXT    DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_fact_date     ON fact_sales(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_product  ON fact_sales(product_key);
CREATE INDEX IF NOT EXISTS idx_fact_customer ON fact_sales(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_country  ON fact_sales(country_key);
CREATE INDEX IF NOT EXISTS idx_dim_date_ym   ON dim_date(year_month);
"""

COUNTRY_REGIONS = {
    "United Kingdom": "Europe",    "EIRE": "Europe",
    "Germany": "Europe",           "France": "Europe",
    "Netherlands": "Europe",       "Spain": "Europe",
    "Belgium": "Europe",           "Switzerland": "Europe",
    "Portugal": "Europe",          "Norway": "Europe",
    "Finland": "Europe",           "Sweden": "Europe",
    "Denmark": "Europe",           "Italy": "Europe",
    "Austria": "Europe",           "Poland": "Europe",
    "Cyprus": "Europe",            "Greece": "Europe",
    "Iceland": "Europe",           "Malta": "Europe",
    "Lithuania": "Europe",
    "Australia": "Asia-Pacific",   "Japan": "Asia-Pacific",
    "Singapore": "Asia-Pacific",   "Hong Kong": "Asia-Pacific",
    "Bahrain": "Asia-Pacific",     "Saudi Arabia": "Asia-Pacific",
    "Lebanon": "Asia-Pacific",     "United Arab Emirates": "Asia-Pacific",
    "USA": "Americas",             "Canada": "Americas",
    "Brazil": "Americas",
}


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)
    conn.commit()
    print("Schema created.")


# ── Dim loaders ───────────────────────────────────────────────

def load_dim_date(df: pd.DataFrame, conn: sqlite3.Connection) -> dict:
    """Build date_key = YYYYMMDDhh integer. Returns mapping dict."""
    df["_date_key"] = (
        df["InvoiceDate"].dt.strftime("%Y%m%d%H").astype(int)
    )

    dates = df.drop_duplicates(subset=["_date_key"]).copy()
    dim = pd.DataFrame({
        "date_key"    : dates["_date_key"].values,
        "full_date"   : dates["InvoiceDate"].dt.date.astype(str).values,
        "year"        : dates["InvoiceDate"].dt.year.values,
        "quarter"     : dates["InvoiceDate"].dt.quarter.values,
        "month"       : dates["InvoiceDate"].dt.month.values,
        "month_name"  : dates["InvoiceDate"].dt.month_name().values,
        "week_of_year": dates["InvoiceDate"].dt.isocalendar().week.astype(int).values,
        "day_of_month": dates["InvoiceDate"].dt.day.values,
        "day_of_week" : dates["InvoiceDate"].dt.dayofweek.values,
        "day_name"    : dates["InvoiceDate"].dt.day_name().values,
        "hour"        : dates["InvoiceDate"].dt.hour.values,
        "year_month"  : dates["InvoiceDate"].dt.to_period("M").astype(str).values,
        "is_weekend"  : dates["InvoiceDate"].dt.dayofweek.isin([5, 6]).astype(int).values,
    })
    dim.to_sql("dim_date", conn, if_exists="append", index=False)
    conn.commit()
    print(f"  dim_date     : {len(dim):,} rows")
    return dict(zip(dates["_date_key"], dates["_date_key"]))


def load_dim_product(df: pd.DataFrame, conn: sqlite3.Connection) -> pd.DataFrame:
    products = (
        df.groupby("StockCode")["Description"]
        .agg(lambda x: x.mode()[0] if len(x) > 0 else "Unknown")
        .reset_index()
    )
    products.columns = ["stock_code", "description"]
    products.to_sql("dim_product", conn, if_exists="append", index=False)
    conn.commit()

    # Return with product_key
    dim = pd.read_sql("SELECT product_key, stock_code FROM dim_product", conn)
    print(f"  dim_product  : {len(dim):,} rows")
    return dim


def load_dim_customer(df: pd.DataFrame, conn: sqlite3.Connection) -> pd.DataFrame:
    # Guest placeholder
    conn.execute("INSERT OR IGNORE INTO dim_customer VALUES (-1, -1, 0)")

    customers = (
        df[df["CustomerID"].notna()][["CustomerID"]]
        .drop_duplicates()
        .rename(columns={"CustomerID": "customer_id"})
        .assign(customer_key=lambda x: x["customer_id"].astype(int),
                has_account=1)
    )
    customers.to_sql("dim_customer", conn, if_exists="append", index=False)
    conn.commit()

    dim = pd.read_sql("SELECT customer_key, customer_id FROM dim_customer", conn)
    print(f"  dim_customer : {len(dim):,} rows")
    return dim


def load_dim_country(df: pd.DataFrame, conn: sqlite3.Connection) -> pd.DataFrame:
    countries = df[["Country"]].drop_duplicates()
    countries = countries.rename(columns={"Country": "country_name"})
    countries["region"] = countries["country_name"].map(COUNTRY_REGIONS).fillna("Other")
    countries.to_sql("dim_country", conn, if_exists="append", index=False)
    conn.commit()

    dim = pd.read_sql("SELECT country_key, country_name FROM dim_country", conn)
    print(f"  dim_country  : {len(dim):,} rows")
    return dim


# ── Fact loader ───────────────────────────────────────────────

def load_fact_sales(df: pd.DataFrame, conn: sqlite3.Connection,
                    dim_product, dim_customer, dim_country) -> None:

    prod_map  = dict(zip(dim_product["stock_code"],  dim_product["product_key"]))
    cust_map  = dict(zip(dim_customer["customer_id"].astype("Int64"), dim_customer["customer_key"]))
    co_map    = dict(zip(dim_country["country_name"], dim_country["country_key"]))

    fact = pd.DataFrame({
        "invoice_no"   : df["Invoice"].values,
        "date_key"     : df["InvoiceDate"].dt.strftime("%Y%m%d%H").astype(int).values,
        "product_key"  : df["StockCode"].map(prod_map).values,
        "customer_key" : df["CustomerID"].map(cust_map).fillna(-1).astype(int).values,
        "country_key"  : df["Country"].map(co_map).values,
        "quantity"     : df["Quantity"].values,
        "unit_price"   : df["Price"].values,
        "total_revenue": df["TotalRevenue"].values,
    })

    # Drop rows where FK lookup failed
    before = len(fact)
    fact = fact.dropna(subset=["product_key", "country_key"])
    if before != len(fact):
        print(f"  Dropped {before - len(fact)} rows with missing FK lookups")

    # Insert in chunks to avoid memory issues
    chunk = 50_000
    for i in range(0, len(fact), chunk):
        fact.iloc[i:i+chunk].to_sql("fact_sales", conn, if_exists="append", index=False)
    conn.commit()
    print(f"  fact_sales   : {len(fact):,} rows")


# ── Forecast loader ───────────────────────────────────────────

def load_forecast(conn: sqlite3.Connection) -> None:
    fpath = f"{PROCESSED_DIR}/revenue_forecast.csv"
    if not os.path.exists(fpath):
        print("  revenue_forecast.csv not found — run src/forecasting.py first")
        return
    fc = pd.read_csv(fpath)
    fc.rename(columns={
        "YearMonth": "year_month",
        "ForecastRevenue": "forecast_revenue",
        "Lower_80CI": "lower_80ci",
        "Upper_80CI": "upper_80ci",
        "ModelUsed": "model_used"
    }, inplace=True)
    fc.to_sql("forecast_results", conn, if_exists="append", index=False)
    conn.commit()
    print(f"  forecast_results: {len(fc)} rows")


# ── Validation ────────────────────────────────────────────────

def validate(conn: sqlite3.Connection) -> None:
    print("\n=== ROW COUNTS ===")
    tables = ["dim_date", "dim_product", "dim_customer", "dim_country",
              "fact_sales", "forecast_results"]
    for t in tables:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<20}: {cnt:>10,}")

    print("\n=== QUICK SANITY: monthly revenue ===")
    rows = conn.execute("""
        SELECT d.year_month, ROUND(SUM(f.total_revenue), 0) AS revenue
        FROM fact_sales f
        JOIN dim_date d ON d.date_key = f.date_key
        GROUP BY d.year_month
        ORDER BY d.year_month
        LIMIT 5
    """).fetchall()
    for r in rows:
        print(f"  {r[0]}: £{r[1]:>12,.0f}")


# ── Main ──────────────────────────────────────────────────────

def main():
    print("=== ETL PIPELINE ===\n")

    # Load cleaned data
    print("Loading cleaned_sales.csv ...")
    df = pd.read_csv(f"{PROCESSED_DIR}/cleaned_sales.csv", parse_dates=["InvoiceDate"])
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce").astype("Int64")
    print(f"  {len(df):,} rows loaded")

    conn = get_conn(DB_PATH)

    print("\n[Creating schema]")
    create_schema(conn)

    print("\n[Loading dimensions]")
    load_dim_date(df, conn)
    dim_product  = load_dim_product(df, conn)
    dim_customer = load_dim_customer(df, conn)
    dim_country  = load_dim_country(df, conn)

    print("\n[Loading fact table]")
    load_fact_sales(df, conn, dim_product, dim_customer, dim_country)

    print("\n[Loading forecast results]")
    load_forecast(conn)

    validate(conn)
    conn.close()

    print(f"\n✓ Done. Database: {DB_PATH}")
    print("  Open in DBeaver → File > New Connection > SQLite")
    print("  Open in Power BI → Get Data > SQLite")


if __name__ == "__main__":
    main()
