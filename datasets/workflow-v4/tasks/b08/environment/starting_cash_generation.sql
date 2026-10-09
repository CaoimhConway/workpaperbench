WITH p AS (SELECT * FROM periods WHERE year IN (2024,2025)
UNION ALL SELECT a.year,9,a.gmv_usd_million-q.gmv_usd_million,a.subscription_revenue_usd_million-q.subscription_revenue_usd_million,
a.merchant_revenue_usd_million-q.merchant_revenue_usd_million,a.subscription_cost_usd_million-q.subscription_cost_usd_million,
a.merchant_cost_usd_million-q.merchant_cost_usd_million,a.operating_expense_usd_million-q.operating_expense_usd_million,
a.reported_operating_income_usd_million-q.reported_operating_income_usd_million,a.operating_cash_usd_million-q.operating_cash_usd_million,
a.capex_usd_million-q.capex_usd_million,a.reported_fcf_usd_million-q.reported_fcf_usd_million
FROM periods a JOIN periods q ON a.year=q.year AND a.months=12 AND q.months=3 WHERE a.year IN (2024,2025)) SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,
subscription_revenue_usd_million+merchant_revenue_usd_million revenue_usd_million,operating_cash_usd_million-capex_usd_million fcf_usd_million,
100.0*(operating_cash_usd_million-capex_usd_million)/(subscription_revenue_usd_million+merchant_revenue_usd_million) fcf_margin_pct,
operating_cash_usd_million-capex_usd_million-reported_fcf_usd_million residual_usd_million FROM p
