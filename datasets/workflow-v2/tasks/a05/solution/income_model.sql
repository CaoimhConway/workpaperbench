WITH periods AS (SELECT * FROM income WHERE fiscal_year IN (2024,2025) UNION ALL
SELECT a.fiscal_year,36,a.net_sales_usd_million-q.net_sales_usd_million,a.membership_usd_million-q.membership_usd_million,
a.revenue_usd_million-q.revenue_usd_million,a.merchandise_cost_usd_million-q.merchandise_cost_usd_million,
a.sga_usd_million-q.sga_usd_million,a.operating_income_usd_million-q.operating_income_usd_million
FROM income a JOIN income q ON a.fiscal_year=q.fiscal_year AND a.weeks=52 AND q.weeks=16 WHERE a.fiscal_year IN (2024,2025)) SELECT fiscal_year,weeks,net_sales_usd_million,membership_usd_million,
net_sales_usd_million-merchandise_cost_usd_million merchandise_gross_profit_usd_million,
100.0*(net_sales_usd_million-merchandise_cost_usd_million)/net_sales_usd_million merchandise_gross_margin_pct,
net_sales_usd_million-merchandise_cost_usd_million+membership_usd_million-sga_usd_million operating_income_usd_million,
net_sales_usd_million-merchandise_cost_usd_million+membership_usd_million-sga_usd_million-operating_income_usd_million residual_usd_million FROM periods
