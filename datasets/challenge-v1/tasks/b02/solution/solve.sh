#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "challenge-v1-b02",
  "answers": [
    {
      "id": "march31_reserves_usd",
      "status": "answered",
      "value": 60040707041.0,
      "unit": "usd",
      "reason_code": null,
      "evidence": [
        "b02:s03"
      ],
      "sql": "SELECT SUM(amount_usd) AS value FROM reserve_components WHERE report_date='2025-03-31'"
    },
    {
      "id": "march31_circulation_usdc",
      "status": "answered",
      "value": 59975771715.0,
      "unit": "usdc",
      "reason_code": null,
      "evidence": [
        "b02:s04"
      ],
      "sql": "SELECT SUM(CASE WHEN measure='total supply' THEN amount_usdc ELSE -amount_usdc END) AS value FROM circulation_inputs WHERE report_date='2025-03-31'"
    },
    {
      "id": "march31_residual_usd",
      "status": "answered",
      "value": -1.0,
      "unit": "usd",
      "reason_code": null,
      "evidence": [
        "b02:s03"
      ],
      "sql": "SELECT (SELECT reported_total_usd FROM reported_reserve_totals WHERE report_date='2025-03-31') - SUM(amount_usd) AS value FROM reserve_components WHERE report_date='2025-03-31'"
    },
    {
      "id": "coverage_change_bps",
      "status": "answered",
      "value": -0.15759761976517375,
      "unit": "basis_points",
      "reason_code": null,
      "evidence": [
        "b02:s01",
        "b02:s02",
        "b02:s03",
        "b02:s04"
      ],
      "sql": "WITH a AS (SELECT report_date,SUM(amount_usd) AS assets FROM reserve_components GROUP BY report_date), c AS (SELECT report_date,SUM(CASE WHEN measure='total supply' THEN amount_usdc ELSE -amount_usdc END) AS circulation FROM circulation_inputs GROUP BY report_date) SELECT 10000.0*((SELECT assets*1.0/circulation FROM a JOIN c USING(report_date) WHERE report_date='2025-03-31')-(SELECT assets*1.0/circulation FROM a JOIN c USING(report_date) WHERE report_date='2025-03-19')) AS value"
    }
  ],
  "conclusion": {
    "verdict": "supported",
    "reason_code": "supported_by_calculation",
    "evidence": [
      "b02:s01",
      "b02:s02",
      "b02:s03",
      "b02:s04"
    ]
  }
}
ANSWER
