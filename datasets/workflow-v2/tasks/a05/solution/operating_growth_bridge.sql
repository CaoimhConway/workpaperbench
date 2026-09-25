WITH periods AS (SELECT * FROM income WHERE fiscal_year IN (2024,2025) UNION ALL
SELECT a.fiscal_year,36,a.net_sales_usd_million-q.net_sales_usd_million,a.membership_usd_million-q.membership_usd_million,
a.revenue_usd_million-q.revenue_usd_million,a.merchandise_cost_usd_million-q.merchandise_cost_usd_million,
a.sga_usd_million-q.sga_usd_million,a.operating_income_usd_million-q.operating_income_usd_million
FROM income a JOIN income q ON a.fiscal_year=q.fiscal_year AND a.weeks=52 AND q.weeks=16 WHERE a.fiscal_year IN (2024,2025)) ,components AS (
SELECT fiscal_year,weeks,'merchandise_gross_profit' measure,net_sales_usd_million-merchandise_cost_usd_million amount FROM periods
UNION ALL SELECT fiscal_year,weeks,'membership_fees',membership_usd_million FROM periods
UNION ALL SELECT fiscal_year,weeks,'sga',-sga_usd_million FROM periods)
SELECT c.weeks,c.measure,p.amount prior_usd_million,c.amount current_usd_million,c.amount-p.amount change_usd_million,
100.0*(c.amount-p.amount)/(ct.operating_income_usd_million-pt.operating_income_usd_million) contribution_to_operating_growth_pct
FROM components c JOIN components p ON c.fiscal_year=2025 AND p.fiscal_year=2024 AND c.weeks=p.weeks AND c.measure=p.measure
JOIN periods ct ON ct.fiscal_year=2025 AND ct.weeks=c.weeks JOIN periods pt ON pt.fiscal_year=2024 AND pt.weeks=c.weeks
