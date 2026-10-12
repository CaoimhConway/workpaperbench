WITH m AS (
  SELECT * FROM reserve_reports WHERE report_date = '2025-05-31'
),
j AS (
  SELECT * FROM reserve_reports WHERE report_date = '2025-06-30'
),
cov_m AS (
  SELECT CAST((cash_equivalents_usd + us_government_debt_usd) AS REAL) / issued_sbc * 100.0 AS coverage_pct
  FROM m
),
cov_j AS (
  SELECT CAST((cash_equivalents_usd + us_government_debt_usd) AS REAL) / issued_sbc * 100.0 AS coverage_pct
  FROM j
)
SELECT
  '2025-05-31' AS prior_date,
  '2025-06-30' AS current_date,
  CAST(j.cash_equivalents_usd - m.cash_equivalents_usd AS REAL) AS cash_change_usd,
  CAST(j.us_government_debt_usd - m.us_government_debt_usd AS REAL) AS debt_change_usd,
  CAST(j.reported_reserve_fv_usd - m.reported_reserve_fv_usd AS REAL) AS reserve_change_usd,
  j.issued_sbc - m.issued_sbc AS circulation_change_sbc,
  ROUND((cov_j.coverage_pct - cov_m.coverage_pct) * 10000, 6) AS coverage_change_bps
FROM m, j, cov_m, cov_j;
