WITH w AS (SELECT r.year,r.quarter,SUM(q.revenue_usd_million) revenue,SUM(q.operating_cash_usd_million-q.capex_usd_million) fcf,
r.reported_ttm_revenue_usd_million reported_revenue,r.reported_ttm_fcf_usd_million reported_fcf FROM rolling_disclosures r JOIN quarters q
ON q.year*4+q.quarter BETWEEN r.year*4+r.quarter-3 AND r.year*4+r.quarter WHERE r.year=2025 GROUP BY r.year,r.quarter)
SELECT CAST(year AS INTEGER) year,CAST(quarter AS INTEGER) quarter,revenue ttm_revenue_usd_million,fcf ttm_fcf_usd_million,
100.0*fcf/revenue ttm_fcf_margin_pct,revenue-reported_revenue revenue_residual_usd_million,fcf-reported_fcf fcf_residual_usd_million FROM w
