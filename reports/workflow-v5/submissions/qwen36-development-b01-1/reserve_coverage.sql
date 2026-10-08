SELECT
  r.report_date,
  r.cash_equivalents_usd + r.us_government_debt_usd AS reserves_usd,
  r.issued_sbc,
  100.0 * (r.cash_equivalents_usd + r.us_government_debt_usd) / r.issued_sbc AS coverage_pct,
  (r.cash_equivalents_usd + r.us_government_debt_usd) - r.reported_reserve_fv_usd AS residual_usd
FROM reserve_reports r
WHERE r.report_date IN ('2025-05-31', '2025-06-30')
