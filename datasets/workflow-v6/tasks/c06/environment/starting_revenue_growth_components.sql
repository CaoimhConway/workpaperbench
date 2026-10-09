WITH total AS (SELECT SUM(CASE WHEN year=2025 THEN revenue_usd_million WHEN year=2024 THEN -revenue_usd_million ELSE 0 END) delta FROM revenue_components)
SELECT c.measure,p.revenue_usd_million prior_usd_million,c.revenue_usd_million current_usd_million,c.revenue_usd_million-p.revenue_usd_million change_usd_million,
100.0*(c.revenue_usd_million-p.revenue_usd_million)/total.delta contribution_to_reported_growth_pct FROM revenue_components c
JOIN revenue_components p ON p.measure=c.measure AND p.year=2024 AND c.year=2025 CROSS JOIN total
