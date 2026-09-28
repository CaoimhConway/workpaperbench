WITH p AS (SELECT period,MAX(CASE WHEN measure='gaap' THEN amount_usd_million END) g,
MAX(CASE WHEN measure='adjusted' THEN amount_usd_million END) a FROM net_income_reconciliation GROUP BY period)
SELECT CASE WHEN c.period='FY2025' THEN 'FY' ELSE 'Q4FY' END window,c.g-p.g gaap_change_usd_million,c.a-p.a adjusted_change_usd_million,
100.0*(c.g/p.g-1) gaap_growth_pct,100.0*(c.a/p.a-1) adjusted_growth_pct,(c.a-c.g)-(p.a-p.g) gap_change_usd_million
FROM p c JOIN p p ON (c.period='FY2025' AND p.period='FY2024') OR (c.period='Q4FY2025' AND p.period='Q4FY2024')
