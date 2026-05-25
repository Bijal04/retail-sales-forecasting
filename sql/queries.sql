-- ============================================================
-- queries.sql  |  Reporting queries for Power BI & analysis
-- ============================================================
-- All queries work directly against the star schema.
-- Use as DirectQuery sources or copy into Power BI / DBeaver.
-- ============================================================


-- ══════════════════════════════════════════════════════════════
-- 1. MONTHLY REVENUE SUMMARY  (main KPI line chart)
-- ══════════════════════════════════════════════════════════════

SELECT
    d.year_month,
    d.year,
    d.month,
    d.month_name,
    SUM(f.total_revenue)            AS total_revenue,
    SUM(f.quantity)                 AS total_units_sold,
    COUNT(DISTINCT f.invoice_no)    AS num_invoices,
    COUNT(DISTINCT f.customer_key)  AS num_customers,
    COUNT(DISTINCT f.product_key)   AS num_products,
    SUM(f.total_revenue) /
        NULLIF(COUNT(DISTINCT f.invoice_no), 0) AS avg_order_value
FROM fact_sales  f
JOIN dim_date    d ON d.date_key = f.date_key
GROUP BY d.year_month, d.year, d.month, d.month_name
ORDER BY d.year_month;


-- ══════════════════════════════════════════════════════════════
-- 2. REVENUE vs FORECAST  (actual vs predicted side-by-side)
-- ══════════════════════════════════════════════════════════════

SELECT
    COALESCE(a.year_month, fr.year_month)  AS year_month,
    a.actual_revenue,
    fr.forecast_revenue,
    fr.lower_80ci,
    fr.upper_80ci,
    fr.model_used,
    CASE
      WHEN a.actual_revenue IS NULL THEN 'Forecast'
      ELSE 'Actual'
    END AS data_type
FROM (
    SELECT d.year_month, SUM(f.total_revenue) AS actual_revenue
    FROM fact_sales f
    JOIN dim_date   d ON d.date_key = f.date_key
    GROUP BY d.year_month
) a
FULL OUTER JOIN forecast_results fr ON fr.year_month = a.year_month
ORDER BY COALESCE(a.year_month, fr.year_month);


-- ══════════════════════════════════════════════════════════════
-- 3. YEAR-OVER-YEAR GROWTH
-- ══════════════════════════════════════════════════════════════

WITH monthly AS (
    SELECT
        d.year,
        d.month,
        SUM(f.total_revenue) AS revenue
    FROM fact_sales f
    JOIN dim_date   d ON d.date_key = f.date_key
    GROUP BY d.year, d.month
)
SELECT
    curr.year,
    curr.month,
    curr.revenue                                          AS current_revenue,
    prev.revenue                                          AS prev_year_revenue,
    ROUND(
        (curr.revenue - prev.revenue) / NULLIF(prev.revenue, 0) * 100, 2
    )                                                     AS yoy_growth_pct
FROM monthly curr
LEFT JOIN monthly prev
  ON prev.year  = curr.year - 1
 AND prev.month = curr.month
ORDER BY curr.year, curr.month;


-- ══════════════════════════════════════════════════════════════
-- 4. TOP 20 PRODUCTS BY REVENUE
-- ══════════════════════════════════════════════════════════════

SELECT
    p.stock_code,
    p.description,
    SUM(f.total_revenue)           AS total_revenue,
    SUM(f.quantity)                AS total_units,
    COUNT(DISTINCT f.invoice_no)   AS num_orders,
    ROUND(AVG(f.unit_price), 2)    AS avg_unit_price,
    COUNT(DISTINCT f.customer_key) AS unique_customers
FROM fact_sales   f
JOIN dim_product  p ON p.product_key = f.product_key
GROUP BY p.stock_code, p.description
ORDER BY total_revenue DESC
LIMIT 20;


-- ══════════════════════════════════════════════════════════════
-- 5. REVENUE BY COUNTRY
-- ══════════════════════════════════════════════════════════════

SELECT
    co.country_name,
    co.region,
    SUM(f.total_revenue)           AS total_revenue,
    SUM(f.quantity)                AS total_units,
    COUNT(DISTINCT f.customer_key) AS num_customers,
    COUNT(DISTINCT f.invoice_no)   AS num_invoices,
    ROUND(
        SUM(f.total_revenue) * 100.0 /
        SUM(SUM(f.total_revenue)) OVER (), 2
    )                              AS revenue_pct
FROM fact_sales   f
JOIN dim_country  co ON co.country_key = f.country_key
GROUP BY co.country_name, co.region
ORDER BY total_revenue DESC;


-- ══════════════════════════════════════════════════════════════
-- 6. REVENUE BY DAY OF WEEK & HOUR  (heatmap data)
-- ══════════════════════════════════════════════════════════════

SELECT
    d.day_name,
    d.day_of_week,
    d.hour,
    SUM(f.total_revenue)         AS total_revenue,
    COUNT(DISTINCT f.invoice_no) AS num_invoices,
    ROUND(AVG(f.total_revenue), 2) AS avg_line_revenue
FROM fact_sales f
JOIN dim_date   d ON d.date_key = f.date_key
GROUP BY d.day_name, d.day_of_week, d.hour
ORDER BY d.day_of_week, d.hour;


-- ══════════════════════════════════════════════════════════════
-- 7. CUSTOMER SEGMENTATION (RFM — Recency, Frequency, Monetary)
-- ══════════════════════════════════════════════════════════════

WITH rfm_raw AS (
    SELECT
        f.customer_key,
        MAX(d.full_date)               AS last_purchase_date,
        COUNT(DISTINCT f.invoice_no)   AS frequency,
        SUM(f.total_revenue)           AS monetary
    FROM fact_sales f
    JOIN dim_date   d ON d.date_key = f.date_key
    WHERE f.customer_key <> -1         -- exclude guest orders
    GROUP BY f.customer_key
),
max_date AS (SELECT MAX(last_purchase_date) AS ref_date FROM rfm_raw),
rfm_scored AS (
    SELECT
        r.customer_key,
        r.last_purchase_date,
        (m.ref_date - r.last_purchase_date) AS recency_days,
        r.frequency,
        r.monetary,
        NTILE(5) OVER (ORDER BY (m.ref_date - r.last_purchase_date) ASC)  AS r_score,
        NTILE(5) OVER (ORDER BY r.frequency                         ASC)  AS f_score,
        NTILE(5) OVER (ORDER BY r.monetary                          ASC)  AS m_score
    FROM rfm_raw r, max_date m
)
SELECT
    customer_key,
    last_purchase_date,
    recency_days,
    frequency,
    ROUND(monetary::NUMERIC, 2)         AS monetary,
    r_score,
    f_score,
    m_score,
    ROUND((r_score + f_score + m_score) / 3.0, 1) AS rfm_score,
    CASE
      WHEN (r_score + f_score + m_score) >= 12 THEN 'Champions'
      WHEN (r_score + f_score + m_score) >= 9  THEN 'Loyal'
      WHEN r_score >= 4                        THEN 'Recent'
      WHEN f_score >= 4                        THEN 'Frequent'
      WHEN (r_score + f_score + m_score) <= 5  THEN 'At Risk'
      ELSE 'Potential'
    END                                 AS segment
FROM rfm_scored
ORDER BY rfm_score DESC;


-- ══════════════════════════════════════════════════════════════
-- 8. MONTHLY PRODUCT CATEGORY PERFORMANCE
--    (for per-category forecasting in Power BI)
-- ══════════════════════════════════════════════════════════════

SELECT
    d.year_month,
    p.stock_code,
    p.description,
    SUM(f.total_revenue)  AS revenue,
    SUM(f.quantity)       AS units_sold,
    COUNT(f.invoice_no)   AS num_line_items
FROM fact_sales  f
JOIN dim_date    d ON d.date_key    = f.date_key
JOIN dim_product p ON p.product_key = f.product_key
GROUP BY d.year_month, p.stock_code, p.description
ORDER BY d.year_month, revenue DESC;


-- ══════════════════════════════════════════════════════════════
-- 9. INVENTORY RISK FLAGS  (Power BI conditional formatting)
-- ══════════════════════════════════════════════════════════════

SELECT
    ir.stock_code,
    ir.description,
    ir.avg_monthly_qty,
    ir.forecast_qty,
    ir.stockout_flag,
    ir.risk_level,
    -- Join with last 3 months actuals for trend
    recent.last_3m_avg_qty,
    CASE
      WHEN recent.last_3m_avg_qty > ir.avg_monthly_qty * 1.2
        THEN 'DEMAND RISING'
      WHEN recent.last_3m_avg_qty < ir.avg_monthly_qty * 0.8
        THEN 'DEMAND FALLING'
      ELSE 'STABLE'
    END AS demand_trend
FROM inventory_risk ir
LEFT JOIN (
    SELECT
        p.stock_code,
        ROUND(AVG(monthly.qty), 0) AS last_3m_avg_qty
    FROM dim_product p
    JOIN (
        SELECT f.product_key, d.year_month, SUM(f.quantity) AS qty
        FROM fact_sales f
        JOIN dim_date d ON d.date_key = f.date_key
        WHERE d.full_date >= CURRENT_DATE - INTERVAL '3 months'
        GROUP BY f.product_key, d.year_month
    ) monthly ON monthly.product_key = p.product_key
    GROUP BY p.stock_code
) recent ON recent.stock_code = ir.stock_code
ORDER BY
    CASE ir.risk_level WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
    ir.avg_monthly_qty DESC;


-- ══════════════════════════════════════════════════════════════
-- 10. POWER BI KPI CARD VALUES  (single-row summary)
-- ══════════════════════════════════════════════════════════════

SELECT
    SUM(f.total_revenue)                   AS total_revenue_all_time,
    COUNT(DISTINCT f.invoice_no)           AS total_invoices,
    COUNT(DISTINCT f.customer_key)
      FILTER (WHERE f.customer_key <> -1) AS total_customers,
    COUNT(DISTINCT f.product_key)          AS total_products,
    ROUND(
        SUM(f.total_revenue) /
        NULLIF(COUNT(DISTINCT f.invoice_no), 0), 2
    )                                      AS avg_order_value,
    -- Last 30 days revenue
    SUM(f.total_revenue)
      FILTER (WHERE d.full_date >= CURRENT_DATE - INTERVAL '30 days')
                                           AS revenue_last_30d,
    -- Last 30 days invoice count
    COUNT(DISTINCT f.invoice_no)
      FILTER (WHERE d.full_date >= CURRENT_DATE - INTERVAL '30 days')
                                           AS invoices_last_30d
FROM fact_sales f
JOIN dim_date   d ON d.date_key = f.date_key;
