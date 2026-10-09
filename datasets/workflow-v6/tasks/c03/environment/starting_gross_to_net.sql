WITH p AS (SELECT period,
SUM(CASE WHEN measure IN ('service','data_processing','international','other') THEN amount_usd_million ELSE 0 END) g,
MAX(CASE WHEN measure='client_incentives' THEN amount_usd_million END) i,
MAX(CASE WHEN measure='net_revenue' THEN amount_usd_million END) n FROM revenue_components WHERE period IN ('FY2025','Q4FY2025') GROUP BY period),
periods AS (SELECT * FROM p UNION ALL SELECT '9MFY2025',a.g-q.g,a.i-q.i,a.n-q.n FROM p a JOIN p q ON a.period='FY2025' AND q.period='Q4FY2025')
SELECT period,g gross_revenue_usd_million,i incentives_usd_million,g-i net_revenue_usd_million,-100.0*i/g incentive_share_of_gross_pct,g+i-n residual_usd_million FROM periods
