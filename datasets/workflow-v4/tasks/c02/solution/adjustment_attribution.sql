WITH p AS (SELECT measure,
MAX(CASE WHEN period='FY2024' THEN amount END) prior,
MAX(CASE WHEN period='FY2025' THEN amount END) current
FROM operating_reconciliation WHERE period IN ('FY2024','FY2025') GROUP BY measure),
t AS (SELECT (SELECT current-prior FROM p WHERE measure='non_gaap_operating_income')-
(SELECT current-prior FROM p WHERE measure='gaap_operating_income') gap_delta)
SELECT measure,prior prior_usd_million,current current_usd_million,current-prior change_usd_million,
100.0*(current-prior)/t.gap_delta contribution_to_gap_change_pct FROM p CROSS JOIN t
WHERE measure NOT IN ('gaap_operating_income','non_gaap_operating_income')
