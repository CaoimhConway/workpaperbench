WITH p AS (SELECT * FROM segments WHERE fiscal_year IN (2024,2025)),periods AS (SELECT * FROM p UNION ALL
SELECT a.fiscal_year,9,a.segment,a.revenue_usd_million-q.revenue_usd_million,a.operating_income_usd_million-q.operating_income_usd_million
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.segment=q.segment AND a.months=12 AND q.months=3) SELECT fiscal_year,months,segment,revenue_usd_million,operating_income_usd_million,100.0*operating_income_usd_million/revenue_usd_million margin_pct FROM periods
