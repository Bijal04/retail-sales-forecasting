-- ============================================================
-- schema.sql  |  Star Schema DDL for Online Retail II
-- ============================================================
-- Fact table : fact_sales
-- Dimensions : dim_date, dim_product, dim_customer, dim_country
-- ============================================================

-- ── Drop in reverse dependency order ─────────────────────────
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_country;
DROP TABLE IF EXISTS dim_date;

-- ── dim_date ─────────────────────────────────────────────────
CREATE TABLE dim_date (
    date_key        INTEGER      PRIMARY KEY,   -- YYYYMMDD  e.g. 20101201
    full_date       DATE         NOT NULL,
    year            SMALLINT     NOT NULL,
    quarter         SMALLINT     NOT NULL,       -- 1-4
    month           SMALLINT     NOT NULL,       -- 1-12
    month_name      VARCHAR(10)  NOT NULL,       -- 'January' … 'December'
    week_of_year    SMALLINT     NOT NULL,       -- ISO week 1-53
    day_of_month    SMALLINT     NOT NULL,       -- 1-31
    day_of_week     SMALLINT     NOT NULL,       -- 0=Mon … 6=Sun
    day_name        VARCHAR(10)  NOT NULL,       -- 'Monday' … 'Sunday'
    hour            SMALLINT     NOT NULL,       -- 0-23
    year_month      CHAR(7)      NOT NULL,       -- 'YYYY-MM'  for easy grouping
    is_weekend      BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_dim_date_year_month ON dim_date (year_month);
CREATE INDEX idx_dim_date_year       ON dim_date (year);
CREATE INDEX idx_dim_date_month      ON dim_date (month);

-- ── dim_product ───────────────────────────────────────────────
CREATE TABLE dim_product (
    product_key     SERIAL       PRIMARY KEY,
    stock_code      VARCHAR(20)  NOT NULL UNIQUE,
    description     VARCHAR(255) NOT NULL DEFAULT 'Unknown',
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_product_stock_code ON dim_product (stock_code);

-- ── dim_customer ─────────────────────────────────────────────
CREATE TABLE dim_customer (
    customer_key    INTEGER      PRIMARY KEY,   -- equals CustomerID from source
    customer_id     INTEGER      NOT NULL UNIQUE,
    has_account     BOOLEAN      NOT NULL DEFAULT TRUE,  -- FALSE for guest (-1)
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Guest / anonymous placeholder
INSERT INTO dim_customer (customer_key, customer_id, has_account)
VALUES (-1, -1, FALSE);

-- ── dim_country ───────────────────────────────────────────────
CREATE TABLE dim_country (
    country_key     SERIAL       PRIMARY KEY,
    country_name    VARCHAR(100) NOT NULL UNIQUE,
    region          VARCHAR(50)  NOT NULL DEFAULT 'Other'  -- e.g. 'Europe', 'Other'
);

-- ── fact_sales ────────────────────────────────────────────────
CREATE TABLE fact_sales (
    sale_id         BIGSERIAL    PRIMARY KEY,
    invoice_no      VARCHAR(20)  NOT NULL,
    date_key        INTEGER      NOT NULL REFERENCES dim_date    (date_key),
    product_key     INTEGER      NOT NULL REFERENCES dim_product (product_key),
    customer_key    INTEGER      NOT NULL REFERENCES dim_customer(customer_key),
    country_key     INTEGER      NOT NULL REFERENCES dim_country (country_key),

    -- Measures
    quantity        INTEGER      NOT NULL,
    unit_price      NUMERIC(10,4) NOT NULL,
    total_revenue   NUMERIC(12,2) NOT NULL,   -- quantity * unit_price

    -- Audit
    loaded_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX idx_fact_sales_date_key     ON fact_sales (date_key);
CREATE INDEX idx_fact_sales_product_key  ON fact_sales (product_key);
CREATE INDEX idx_fact_sales_customer_key ON fact_sales (customer_key);
CREATE INDEX idx_fact_sales_country_key  ON fact_sales (country_key);
CREATE INDEX idx_fact_sales_invoice      ON fact_sales (invoice_no);
CREATE INDEX idx_fact_sales_year_month   ON fact_sales (date_key)
    WHERE date_key > 0;  -- partial index for fast monthly roll-ups

-- ── Forecast results table (populated from Python) ───────────
DROP TABLE IF EXISTS forecast_results;
CREATE TABLE forecast_results (
    forecast_id     SERIAL       PRIMARY KEY,
    year_month      CHAR(7)      NOT NULL UNIQUE,
    forecast_revenue NUMERIC(14,2) NOT NULL,
    lower_80ci      NUMERIC(14,2),
    upper_80ci      NUMERIC(14,2),
    model_used      VARCHAR(50),
    generated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Inventory risk staging table ─────────────────────────────
DROP TABLE IF EXISTS inventory_risk;
CREATE TABLE inventory_risk (
    risk_id         SERIAL       PRIMARY KEY,
    stock_code      VARCHAR(20)  NOT NULL,
    description     VARCHAR(255),
    avg_monthly_qty INTEGER,
    forecast_qty    INTEGER,
    stockout_flag   BOOLEAN      NOT NULL DEFAULT FALSE,  -- TRUE if forecast > avg_stock
    risk_level      VARCHAR(10)  CHECK (risk_level IN ('LOW','MEDIUM','HIGH')),
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Quick schema summary ─────────────────────────────────────
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
