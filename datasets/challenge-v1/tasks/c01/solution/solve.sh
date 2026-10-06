#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "answers": [
    {
      "evidence": [
        "c01:s01",
        "c01:s03",
        "c01:s06"
      ],
      "id": "yield_2024",
      "reason_code": null,
      "sql": "SELECT 100.0*(SELECT amount FROM revenues WHERE period_end='2024-12-31' AND months=12 AND category='Transaction revenues')/(SELECT amount FROM operating_metrics WHERE period_end='2024-12-31' AND months=12 AND metric='Total payment volume')",
      "status": "answered",
      "unit": "percent",
      "value": 1.715611337477322
    },
    {
      "evidence": [
        "c01:s01",
        "c01:s03",
        "c01:s06"
      ],
      "id": "yield_2023",
      "reason_code": null,
      "sql": "SELECT 100.0*(SELECT amount FROM revenues WHERE period_end='2023-12-31' AND months=12 AND category='Transaction revenues')/(SELECT amount FROM operating_metrics WHERE period_end='2023-12-31' AND months=12 AND metric='Total payment volume')",
      "status": "answered",
      "unit": "percent",
      "value": 1.7569912971459114
    },
    {
      "evidence": [
        "c01:s01",
        "c01:s03",
        "c01:s06"
      ],
      "id": "yield_change",
      "reason_code": null,
      "sql": "SELECT 10000.0*((SELECT amount FROM revenues WHERE period_end='2024-12-31' AND months=12 AND category='Transaction revenues')/(SELECT amount FROM operating_metrics WHERE period_end='2024-12-31' AND months=12 AND metric='Total payment volume')-(SELECT amount FROM revenues WHERE period_end='2023-12-31' AND months=12 AND category='Transaction revenues')/(SELECT amount FROM operating_metrics WHERE period_end='2023-12-31' AND months=12 AND metric='Total payment volume'))",
      "status": "answered",
      "unit": "basis_points",
      "value": -4.137995966858926
    },
    {
      "evidence": [
        "c01:s01",
        "c01:s06"
      ],
      "id": "transaction_contribution",
      "reason_code": null,
      "sql": "SELECT 100.0*((SELECT amount FROM revenues WHERE period_end='2024-12-31' AND months=12 AND category='Transaction revenues')-(SELECT amount FROM revenues WHERE period_end='2023-12-31' AND months=12 AND category='Transaction revenues'))/((SELECT amount FROM revenues WHERE period_end='2024-12-31' AND months=12 AND category='Total net revenues (2)')-(SELECT amount FROM revenues WHERE period_end='2023-12-31' AND months=12 AND category='Total net revenues (2)'))",
      "status": "answered",
      "unit": "percent",
      "value": 97.97630799605133
    }
  ],
  "conclusion": {
    "evidence": [
      "c01:s01",
      "c01:s03",
      "c01:s06"
    ],
    "reason_code": null,
    "verdict": "contradicted"
  },
  "task_id": "challenge-v1-c01"
}
ANSWER
