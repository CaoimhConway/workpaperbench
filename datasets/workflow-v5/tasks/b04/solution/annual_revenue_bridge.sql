WITH p AS (SELECT * FROM revenues WHERE period='FY2024'),c AS (SELECT * FROM revenues WHERE period='FY2025'),
components AS (SELECT 'transaction' measure,p.transaction_usd_million prior,c.transaction_usd_million current FROM p CROSS JOIN c
UNION ALL SELECT 'interest',p.interest_usd_million,c.interest_usd_million FROM p CROSS JOIN c
UNION ALL SELECT 'other',p.other_usd_million,c.other_usd_million FROM p CROSS JOIN c)
SELECT measure,prior prior_usd_million,current current_usd_million,current-prior change_usd_million,
100.0*(current-prior)/(c.total_usd_million-p.total_usd_million) contribution_to_total_growth_pct FROM components CROSS JOIN p CROSS JOIN c
