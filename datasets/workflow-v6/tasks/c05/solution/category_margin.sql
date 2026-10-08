WITH p AS (SELECT year,months,'product' category,product_revenue_usd_million r,product_cost_usd_million c FROM income
UNION ALL SELECT year,months,'service',service_revenue_usd_million,service_cost_usd_million FROM income)
SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,category,r-c gross_profit_usd_million,100.0*(r-c)/r margin_pct FROM p WHERE year IN (2024,2025)
