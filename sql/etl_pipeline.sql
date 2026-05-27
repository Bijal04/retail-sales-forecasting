-- ============================================================
-- etl_pipeline.sql  |  ETL queries to load cleaned CSV data
-- ============================================================
-- Run order:
--   1. schema.sql  (create tables)
--   2. etl_pipeline.sql  (load data)
--   3. queries.sql  (reporting)
--
-- Replace '<path>' with absolute path to your processed/ folder
-- e.g. /home/user/retail-sales-forecasting/data/processed/
-- ============================================================


-- ══════════════════════════════════════════════════════════════
-- STEP 1 — LOAD dim_country
-- ══════════════════════════════════════════════════════════════

-- Load distinct countries from cleaned CSV
-- In PostgreSQL use \COPY; in SQLite use .import

-- PostgreSQL:
/*
\COPY (
  SELECT DISTINCT
    country,
    CASE
      WHEN country IN ('United Kingdom','EIRE','Germany','France','Netherlands',
                       'Spain','Belgium','Switzerland','Portugal','Norway',
                       'Finland','Sweden','Denmark','Italy','Austria','Poland',
                       'Cyprus','Greece','Iceland','Malta','Lithuania') THEN 'Europe'
      WHEN country IN ('Australia','Japan','Singapore','Hong Kong','Bahrain',
                       'Saudi Arabia','Lebanon','United Arab Emirates') THEN 'Asia-Pacific'
      WHEN country IN ('USA','Canada','Brazil') THEN 'Americas'
      ELSE 'Other'
    END AS region
  FROM staging_sales
  ORDER BY country
) TO '/tmp/countries.csv' CSV HEADER;
*/

-- Manual insert (works for SQLite and any DB)
INSERT INTO dim_country (country_name, region) VALUES
  ('United Kingdom',    'Europe'),
  ('EIRE',              'Europe'),
  ('Germany',           'Europe'),
  ('France',            'Europe'),
  ('Netherlands',       'Europe'),
  ('Spain',             'Europe'),
  ('Belgium',           'Europe'),
  ('Switzerland',       'Europe'),
  ('Portugal',          'Europe'),
  ('Norway',            'Europe'),
  ('Finland',           'Europe'),
  ('Sweden',            'Europe'),
  ('Denmark',           'Europe'),
  ('Italy',             'Europe'),
  ('Austria',           'Europe'),
  ('Poland',            'Europe'),
  ('Cyprus',            'Europe'),
  ('Greece',            'Europe'),
  ('Iceland',           'Europe'),
  ('Malta',             'Europe'),
  ('Lithuania',         'Europe'),
  ('Australia',         'Asia-Pacific'),
  ('Japan',             'Asia-Pacific'),
  ('Singapore',         'Asia-Pacific'),
  ('Hong Kong',         'Asia-Pacific'),
  ('Bahrain',           'Asia-Pacific'),
  ('Saudi Arabia',      'Asia-Pacific'),
  ('Lebanon',           'Asia-Pacific'),
  ('United Arab Emirates','Asia-Pacific'),
  ('USA',               'Americas'),
  ('Canada',            'Americas'),
  ('Brazil',            'Americas'),
  ('Unspecified',       'Other'),
  ('RSA',               'Other')
ON CONFLICT (country_name) DO NOTHING;


-- ══════════════════════════════════════════════════════════════
-- STEP 2 — STAGING TABLE  (load raw CSV here first)
-- ══════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS staging_sales;

CREATE TABLE staging_sales (
    invoice       TEXT,
    stock_code    TEXT,
    description   TEXT,
    quantity      INTEGER,
    invoice_date  TIMESTAMP,
    price         NUMERIC(10,4),
    customer_id   INTEGER,
    country       TEXT,
    total_revenue NUMERIC(12,2),
    year          SMALLINT,
    month         SMALLINT,
    year_month    CHAR(7),
    day_of_week   SMALLINT,
    day_name      TEXT,
    hour          SMALLINT,
    quarter       SMALLINT,
    week_of_year  SMALLINT,
    is_cancelled  BOOLEAN,
    has_customer_id BOOLEAN
);

-- PostgreSQL bulk load:
-- \COPY staging_sales FROM '<path>/cleaned_sales.csv' CSV HEADER NULL '';

-- SQLite equivalent (run in shell):
-- sqlite3 retail.db ".mode csv" ".headers on" ".import <path>/cleaned_sales.csv staging_sales"


-- ══════════════════════════════════════════════════════════════
-- STEP 3 — POPULATE dim_date
-- ══════════════════════════════════════════════════════════════

INSERT INTO dim_date (
    date_key, full_date, year, quarter, month, month_name,
    week_of_year, day_of_month, day_of_week, day_name, hour, year_month, is_weekend
)
SELECT DISTINCT
    CAST(TO_CHAR(invoice_date, 'YYYYMMDDHH24') AS INTEGER)  AS date_key,
    CAST(invoice_date AS DATE)                               AS full_date,
    EXTRACT(YEAR    FROM invoice_date)::SMALLINT             AS year,
    EXTRACT(QUARTER FROM invoice_date)::SMALLINT             AS quarter,
    EXTRACT(MONTH   FROM invoice_date)::SMALLINT             AS month,
    TO_CHAR(invoice_date, 'Month')                           AS month_name,
    EXTRACT(WEEK    FROM invoice_date)::SMALLINT             AS week_of_year,
    EXTRACT(DAY     FROM invoice_date)::SMALLINT             AS day_of_month,
    EXTRACT(DOW     FROM invoice_date)::SMALLINT             AS day_of_week,
    TO_CHAR(invoice_date, 'Day')                             AS day_name,
    EXTRACT(HOUR    FROM invoice_date)::SMALLINT             AS hour,
    TO_CHAR(invoice_date, 'YYYY-MM')                        AS year_month,
    CASE WHEN EXTRACT(DOW FROM invoice_date) IN (0,6) THEN TRUE ELSE FALSE END AS is_weekend
FROM staging_sales
ON CONFLICT (date_key) DO NOTHING;

-- SQLite version (replace EXTRACT / TO_CHAR with strftime):
/*
INSERT OR IGNORE INTO dim_date (
    date_key, full_date, year, quarter, month, month_name,
    week_of_year, day_of_month, day_of_week, day_name, hour, year_month, is_weekend
)
SELECT DISTINCT
    CAST(strftime('%Y%m%d%H', invoice_date) AS INTEGER),
    DATE(invoice_date),
    CAST(strftime('%Y', invoice_date) AS INTEGER),
    (CAST(strftime('%m', invoice_date) AS INTEGER) + 2) / 3,
    CAST(strftime('%m', invoice_date) AS INTEGER),
    CASE strftime('%m', invoice_date)
      WHEN '01' THEN 'January' WHEN '02' THEN 'February' WHEN '03' THEN 'March'
      WHEN '04' THEN 'April'   WHEN '05' THEN 'May'      WHEN '06' THEN 'June'
      WHEN '07' THEN 'July'    WHEN '08' THEN 'August'   WHEN '09' THEN 'September'
      WHEN '10' THEN 'October' WHEN '11' THEN 'November' ELSE 'December'
    END,
    CAST(strftime('%W', invoice_date) AS INTEGER),
    CAST(strftime('%d', invoice_date) AS INTEGER),
    CAST(strftime('%w', invoice_date) AS INTEGER),
    CASE strftime('%w', invoice_date)
      WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday' WHEN '2' THEN 'Tuesday'
      WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'
      ELSE 'Saturday'
    END,
    CAST(strftime('%H', invoice_date) AS INTEGER),
    strftime('%Y-%m', invoice_date),
    CASE WHEN strftime('%w', invoice_date) IN ('0','6') THEN 1 ELSE 0 END
FROM staging_sales;
*/


-- ══════════════════════════════════════════════════════════════
-- STEP 4 — POPULATE dim_product
-- ══════════════════════════════════════════════════════════════

INSERT INTO dim_product (stock_code, description)
SELECT DISTINCT ON (stock_code)
    stock_code,
    COALESCE(description, 'Unknown')
FROM staging_sales
ORDER BY stock_code, description
ON CONFLICT (stock_code) DO UPDATE
    SET description = EXCLUDED.description;

-- SQLite:
/*
INSERT OR IGNORE INTO dim_product (stock_code, description)
SELECT DISTINCT stock_code, COALESCE(description, 'Unknown')
FROM staging_sales;
*/


-- ══════════════════════════════════════════════════════════════
-- STEP 5 — POPULATE dim_customer
-- ══════════════════════════════════════════════════════════════

INSERT INTO dim_customer (customer_key, customer_id, has_account)
SELECT DISTINCT
    customer_id,
    customer_id,
    TRUE
FROM staging_sales
WHERE customer_id IS NOT NULL
ON CONFLICT (customer_id) DO NOTHING;


-- ══════════════════════════════════════════════════════════════
-- STEP 6 — POPULATE fact_sales
-- ══════════════════════════════════════════════════════════════

INSERT INTO fact_sales (
    invoice_no, date_key, product_key, customer_key, country_key,
    quantity, unit_price, total_revenue
)
SELECT
    s.invoice,
    CAST(TO_CHAR(s.invoice_date, 'YYYYMMDDHH24') AS INTEGER)  AS date_key,
    p.product_key,
    COALESCE(c.customer_key, -1)                               AS customer_key,
    co.country_key,
    s.quantity,
    s.price,
    s.total_revenue
FROM staging_sales  s
JOIN  dim_product  p  ON p.stock_code    = s.stock_code
LEFT JOIN dim_customer c  ON c.customer_id   = s.customer_id
JOIN  dim_country  co ON co.country_name  = s.country
JOIN  dim_date     d  ON d.date_key       = CAST(TO_CHAR(s.invoice_date, 'YYYYMMDDHH24') AS INTEGER);


-- ══════════════════════════════════════════════════════════════
-- STEP 7 — LOAD FORECAST RESULTS  (run after notebooks/03)
-- ══════════════════════════════════════════════════════════════

-- \COPY forecast_results (year_month, forecast_revenue, lower_80ci, upper_80ci, model_used)
-- FROM '<path>/revenue_forecast.csv' CSV HEADER;


-- ══════════════════════════════════════════════════════════════
-- STEP 8 — BUILD INVENTORY RISK TABLE
-- ══════════════════════════════════════════════════════════════

INSERT INTO inventory_risk (stock_code, description, avg_monthly_qty, forecast_qty,
                             stockout_flag, risk_level)
SELECT
    p.stock_code,
    p.description,
    AVG(monthly_qty.qty)::INTEGER                     AS avg_monthly_qty,
    NULL                                              AS forecast_qty,
    FALSE                                             AS stockout_flag,
    CASE
      WHEN AVG(monthly_qty.qty) > 1000 THEN 'HIGH'
      WHEN AVG(monthly_qty.qty) > 300  THEN 'MEDIUM'
      ELSE 'LOW'
    END                                               AS risk_level
FROM dim_product p
JOIN (
    SELECT
        f.product_key,
        d.year_month,
        SUM(f.quantity) AS qty
    FROM fact_sales f
    JOIN dim_date d ON d.date_key = f.date_key
    GROUP BY f.product_key, d.year_month
) monthly_qty ON monthly_qty.product_key = p.product_key
GROUP BY p.product_key, p.stock_code, p.description
ON CONFLICT DO NOTHING;


-- ══════════════════════════════════════════════════════════════
-- VALIDATION — row count check after load
-- ══════════════════════════════════════════════════════════════

SELECT 'staging_sales'   AS tbl, COUNT(*) AS rows FROM staging_sales   UNION ALL
SELECT 'fact_sales',              COUNT(*)         FROM fact_sales       UNION ALL
SELECT 'dim_date',                COUNT(*)         FROM dim_date         UNION ALL
SELECT 'dim_product',             COUNT(*)         FROM dim_product      UNION ALL
SELECT 'dim_customer',            COUNT(*)         FROM dim_customer     UNION ALL
SELECT 'dim_country',             COUNT(*)         FROM dim_country      UNION ALL
SELECT 'forecast_results',        COUNT(*)         FROM forecast_results UNION ALL
SELECT 'inventory_risk',          COUNT(*)         FROM inventory_risk;