WITH p AS (SELECT *,product_revenue_usd_million+service_revenue_usd_million-product_cost_usd_million-service_cost_usd_million gp FROM income_versions
WHERE year IN (2024,2025) AND version IN ('release','annual'))
SELECT version,CAST(year AS INTEGER) year,gp gross_profit_usd_million,gp-operating_expense_usd_million operating_income_usd_million,
gp-operating_expense_usd_million+other_income_usd_million pretax_usd_million,
gp-operating_expense_usd_million+other_income_usd_million-tax_usd_million net_income_usd_million,
gp-operating_expense_usd_million+other_income_usd_million-tax_usd_million-net_income_usd_million residual_usd_million FROM p
