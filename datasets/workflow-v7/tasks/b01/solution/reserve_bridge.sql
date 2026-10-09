WITH r AS (SELECT DISTINCT * FROM reserve_reports)
SELECT p.report_date prior_date,c.report_date current_date,
c.cash_equivalents_usd-p.cash_equivalents_usd cash_change_usd,
c.us_government_debt_usd-p.us_government_debt_usd debt_change_usd,
(c.cash_equivalents_usd+c.us_government_debt_usd)-(p.cash_equivalents_usd+p.us_government_debt_usd) reserve_change_usd,
c.issued_sbc-p.issued_sbc circulation_change_sbc,
10000.0*((c.cash_equivalents_usd+c.us_government_debt_usd)*1.0/c.issued_sbc-
(p.cash_equivalents_usd+p.us_government_debt_usd)*1.0/p.issued_sbc) coverage_change_bps
FROM r p CROSS JOIN r c WHERE p.report_date='2025-05-31' AND c.report_date='2025-06-30'
