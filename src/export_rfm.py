import sqlite3, csv

conn = sqlite3.connect('retail_dw.db')
cursor = conn.cursor()

query = """
WITH rfm_raw AS (
    SELECT
        f.customer_key,
        MAX(d.full_date)               AS last_purchase_date,
        COUNT(DISTINCT f.invoice_no)   AS frequency,
        SUM(f.total_revenue)           AS monetary
    FROM fact_sales f
    JOIN dim_date d ON d.date_key = f.date_key
    WHERE f.customer_key <> -1
    GROUP BY f.customer_key
),
max_date AS (SELECT MAX(last_purchase_date) AS ref_date FROM rfm_raw),
rfm_scored AS (
    SELECT
        r.customer_key,
        r.last_purchase_date,
        CAST(JULIANDAY(m.ref_date) - JULIANDAY(r.last_purchase_date) AS INTEGER) AS recency_days,
        r.frequency,
        r.monetary,
        NTILE(5) OVER (ORDER BY (JULIANDAY(m.ref_date) - JULIANDAY(r.last_purchase_date)) ASC) AS r_score,
        NTILE(5) OVER (ORDER BY r.frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY r.monetary  ASC) AS m_score
    FROM rfm_raw r, max_date m
)
SELECT
    customer_key,
    last_purchase_date,
    recency_days,
    frequency,
    ROUND(monetary, 2)                             AS monetary,
    r_score,
    f_score,
    m_score,
    ROUND((r_score + f_score + m_score) / 3.0, 1) AS rfm_score,
    CASE
      WHEN (r_score + f_score + m_score) >= 12 THEN 'Champions'
      WHEN (r_score + f_score + m_score) >= 9  THEN 'Loyal'
      WHEN r_score >= 4                         THEN 'Recent'
      WHEN f_score >= 4                         THEN 'Frequent'
      WHEN (r_score + f_score + m_score) <= 5   THEN 'At Risk'
      ELSE 'Potential'
    END AS segment
FROM rfm_scored
ORDER BY rfm_score DESC
"""

cursor.execute(query)
rows = cursor.fetchall()
headers = [d[0] for d in cursor.description]

with open('data/processed/rfm_segments.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

print(f'Done — {len(rows)} customers exported to data/processed/rfm_segments.csv')
conn.close()