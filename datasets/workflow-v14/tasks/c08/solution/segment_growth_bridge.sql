WITH p AS (SELECT CASE WHEN period LIKE 'Q4%' THEN 'Q4FY' ELSE 'FY' END window,period,segment,revenue_usd_million FROM segments
WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025')),totals AS (SELECT window,SUM(CASE WHEN period LIKE '%2025' THEN revenue_usd_million ELSE -revenue_usd_million END) delta FROM p GROUP BY window)
SELECT c.window,c.segment,p.revenue_usd_million prior_usd_million,c.revenue_usd_million current_usd_million,c.revenue_usd_million-p.revenue_usd_million change_usd_million,
100.0*(c.revenue_usd_million-p.revenue_usd_million)/t.delta contribution_to_total_growth_pct FROM p c JOIN p ON c.window=p.window AND c.segment=p.segment AND c.period LIKE '%2025' AND p.period LIKE '%2024' JOIN totals t ON t.window=c.window
