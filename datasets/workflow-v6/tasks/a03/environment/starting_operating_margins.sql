WITH p AS (SELECT period,
SUM(CASE WHEN measure IN ('reserve_income','other_revenue') THEN amount_usd_thousand ELSE 0 END) r,
SUM(CASE WHEN measure IN ('distribution','other_costs') THEN amount_usd_thousand ELSE 0 END) c,
MAX(CASE WHEN measure='total_revenue' THEN amount_usd_thousand END) reported_r,
MAX(CASE WHEN measure='total_costs' THEN amount_usd_thousand END) reported_c,
MAX(CASE WHEN measure='adjusted_ebitda' THEN amount_usd_thousand END) e
FROM operations WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025') GROUP BY period)
SELECT period,r revenue_usd_thousand,r-c rldc_usd_thousand,100.0*(r-c)/r rldc_margin_pct,
100.0*e/(r-c) adjusted_ebitda_margin_pct,r-reported_r revenue_residual_usd_thousand,c-reported_c cost_residual_usd_thousand FROM p
