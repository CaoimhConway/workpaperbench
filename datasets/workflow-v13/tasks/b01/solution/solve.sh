#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/reserve_coverage.sql <<'SQL'
SELECT DISTINCT report_date,cash_equivalents_usd+us_government_debt_usd reserves_usd,
issued_sbc,100.0*(cash_equivalents_usd+us_government_debt_usd)/issued_sbc coverage_pct,
cash_equivalents_usd+us_government_debt_usd-reported_reserve_fv_usd residual_usd
FROM reserve_reports WHERE report_date IN ('2025-05-31','2025-06-30')
SQL
cat > /logs/artifacts/signature_lag.sql <<'SQL'
SELECT DISTINCT report_date,report_signed_date,
CAST(julianday(report_signed_date)-julianday(report_date) AS INTEGER) days_to_signature
FROM reserve_reports WHERE report_date IN ('2025-05-31','2025-06-30')
SQL
cat > /logs/artifacts/reserve_bridge.sql <<'SQL'
WITH r AS (SELECT DISTINCT * FROM reserve_reports)
SELECT p.report_date prior_date,c.report_date current_date,
c.cash_equivalents_usd-p.cash_equivalents_usd cash_change_usd,
c.us_government_debt_usd-p.us_government_debt_usd debt_change_usd,
(c.cash_equivalents_usd+c.us_government_debt_usd)-(p.cash_equivalents_usd+p.us_government_debt_usd) reserve_change_usd,
c.issued_sbc-p.issued_sbc circulation_change_sbc,
10000.0*((c.cash_equivalents_usd+c.us_government_debt_usd)*1.0/c.issued_sbc-
(p.cash_equivalents_usd+p.us_government_debt_usd)*1.0/p.issued_sbc) coverage_change_bps
FROM r p CROSS JOIN r c WHERE p.report_date='2025-05-31' AND c.report_date='2025-06-30'
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v13-b01",
  "tables": [
    {
      "id": "reserve_coverage",
      "file": "reserve_coverage.sql",
      "evidence": [
        "b01:s01",
        "b01:s04"
      ]
    },
    {
      "id": "signature_lag",
      "file": "signature_lag.sql",
      "evidence": [
        "b01:s03",
        "b01:s06"
      ]
    },
    {
      "id": "reserve_bridge",
      "file": "reserve_bridge.sql",
      "evidence": [
        "b01:s01",
        "b01:s04"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "unresolved",
      "evidence": [
        "b01:s04"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "b01:s03",
        "b01:s06"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "b01:s01",
        "b01:s04"
      ]
    }
  ]
}
ANSWER
