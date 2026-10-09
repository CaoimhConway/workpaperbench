WITH p AS (SELECT version,product_cost_usd_million pc,
product_revenue_usd_million+service_revenue_usd_million-product_cost_usd_million-service_cost_usd_million gp,operating_expense_usd_million e,other_income_usd_million o,tax_usd_million t,net_income_usd_million n FROM income_versions WHERE year=2025),
v AS (SELECT version,'product_cost_usd_million' measure,pc value FROM p UNION ALL SELECT version,'gross_profit_usd_million',gp FROM p
UNION ALL SELECT version,'operating_income_usd_million',gp-e FROM p UNION ALL SELECT version,'pretax_usd_million',gp-e+o FROM p
UNION ALL SELECT version,'tax_usd_million',t FROM p UNION ALL SELECT version,'net_income_usd_million',n FROM p),
b AS (SELECT a.measure,r.value prior_release_usd_million,a.value annual_report_usd_million,a.value-r.value observed_change_usd_million,
CASE WHEN a.measure='product_cost_usd_million' THEN s.product_cost_charge_usd_million WHEN a.measure='tax_usd_million' THEN -s.tax_benefit_usd_million
WHEN a.measure='net_income_usd_million' THEN -s.product_cost_charge_usd_million-s.tax_benefit_usd_million ELSE -s.product_cost_charge_usd_million END settlement_effect_usd_million
FROM v a JOIN v r ON a.measure=r.measure AND a.version='annual' AND r.version='release' CROSS JOIN settlement s WHERE s.fiscal_year_charged=2025)
SELECT *,observed_change_usd_million-settlement_effect_usd_million residual_usd_million FROM b
