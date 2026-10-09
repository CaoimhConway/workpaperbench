WITH p AS (SELECT fiscal_year,months,segment,
MAX(CASE WHEN measure='revenue' THEN amount END) r,
MAX(CASE WHEN measure='operating_income' THEN amount END) oi
FROM segments WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months,segment),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.segment,a.r-q.r,a.oi-q.oi
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.segment=q.segment WHERE a.months=12 AND q.months=3)
SELECT fiscal_year,months,segment,r revenue_usd_million,oi operating_income_usd_million,
100.0*oi/r operating_margin_pct FROM periods
