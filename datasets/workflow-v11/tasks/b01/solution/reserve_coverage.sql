SELECT DISTINCT report_date,cash_equivalents_usd+us_government_debt_usd reserves_usd,
issued_sbc,100.0*(cash_equivalents_usd+us_government_debt_usd)/issued_sbc coverage_pct,
cash_equivalents_usd+us_government_debt_usd-reported_reserve_fv_usd residual_usd
FROM reserve_reports WHERE report_date IN ('2025-05-31','2025-06-30')
