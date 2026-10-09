WITH parts AS (SELECT year,months,'product_gp' measure,product_revenue_usd_million-product_cost_usd_million v FROM income
UNION ALL SELECT year,months,'service_gp',service_revenue_usd_million-service_cost_usd_million FROM income
UNION ALL SELECT year,months,'research',-research_usd_million FROM income
UNION ALL SELECT year,months,'selling',-selling_usd_million FROM income
UNION ALL SELECT year,months,'other',other_income_usd_million FROM income
UNION ALL SELECT year,months,'tax',-tax_usd_million FROM income)
SELECT CAST(c.months AS INTEGER) months,c.measure,p.v prior_signed_usd_million,c.v current_signed_usd_million,c.v-p.v change_usd_million,
100.0*(c.v-p.v)/(ci.net_income_usd_million-pi.net_income_usd_million) contribution_to_net_income_growth_pct
FROM parts c JOIN parts p ON c.measure=p.measure AND c.months=p.months AND c.year=2025 AND p.year=2024
JOIN income ci ON ci.year=c.year AND ci.months=c.months JOIN income pi ON pi.year=p.year AND pi.months=p.months
