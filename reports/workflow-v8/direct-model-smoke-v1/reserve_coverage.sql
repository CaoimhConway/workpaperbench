WITH r AS (
  SELECT
    report_date,
    (cash_equivalents_usd + us_government_debt_usd) AS reserves_usd,
    issued_sbc,
    reported_reserve_fv_usd
  FROM reserve_reports
)
SELECT
  report_date,
  CAST(reserves_usd AS REAL) AS reserves_usd,
  issued_sbc,
  ROUND(CAST(reserves_usd AS REAL) / issued_sbc * 100.0, 6) AS coverage_pct,
  CAST(reserves_usd - reported_reserve_fv_usd AS REAL) AS residual_usd
FROM r;
