#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "challenge-v1-b04",
  "answers": [
    {
      "id": "jun30_reserves_usd",
      "status": "answered",
      "value": 471227699.0,
      "unit": "usd",
      "reason_code": null,
      "evidence": [
        "b04:s04"
      ],
      "sql": "SELECT SUM(amount_usd) AS value FROM reserve_components WHERE report_date='2025-06-30'"
    },
    {
      "id": "jun30_reconciliation_usd",
      "status": "answered",
      "value": 0.0,
      "unit": "usd",
      "reason_code": null,
      "evidence": [
        "b04:s03",
        "b04:s04"
      ],
      "sql": "SELECT (SELECT reported_reserve_usd FROM reported_balances WHERE report_date='2025-06-30') - SUM(amount_usd) AS value FROM reserve_components WHERE report_date='2025-06-30'"
    },
    {
      "id": "coverage_change_bps",
      "status": "answered",
      "value": -71.35472830422277,
      "unit": "basis_points",
      "reason_code": null,
      "evidence": [
        "b04:s01",
        "b04:s02",
        "b04:s03",
        "b04:s04"
      ],
      "sql": "WITH a AS (SELECT report_date,SUM(amount_usd) AS assets FROM reserve_components GROUP BY report_date), b AS (SELECT report_date,circulating_rlusd FROM reported_balances) SELECT 10000.0*((SELECT assets*1.0/circulating_rlusd FROM a JOIN b USING(report_date) WHERE report_date='2025-06-30')-(SELECT assets*1.0/circulating_rlusd FROM a JOIN b USING(report_date) WHERE report_date='2025-05-30')) AS value"
    }
  ],
  "conclusion": {
    "verdict": "contradicted",
    "reason_code": "contradicted_by_calculation",
    "evidence": [
      "b04:s01",
      "b04:s02",
      "b04:s03",
      "b04:s04"
    ]
  }
}
ANSWER
