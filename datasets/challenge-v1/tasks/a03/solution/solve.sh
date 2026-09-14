#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "answers": [
    {
      "evidence": [
        "a03:s02",
        "a03:s03"
      ],
      "id": "q1_revenue",
      "reason_code": null,
      "sql": "WITH x AS (SELECT MAX(CASE WHEN months=3 AND measure='Total revenue' THEN amount END) r2,MAX(CASE WHEN months=6 AND measure='Total revenue' THEN amount END) rh,MAX(CASE WHEN months=3 AND measure='Operating income' THEN amount END) o2,MAX(CASE WHEN months=6 AND measure='Operating income' THEN amount END) oh FROM financials WHERE period_end='2024-12-31') SELECT rh-r2 FROM x",
      "status": "answered",
      "unit": "usd_million",
      "value": 65585.0
    },
    {
      "evidence": [
        "a03:s02",
        "a03:s03"
      ],
      "id": "q1_operating_income",
      "reason_code": null,
      "sql": "WITH x AS (SELECT MAX(CASE WHEN months=3 AND measure='Total revenue' THEN amount END) r2,MAX(CASE WHEN months=6 AND measure='Total revenue' THEN amount END) rh,MAX(CASE WHEN months=3 AND measure='Operating income' THEN amount END) o2,MAX(CASE WHEN months=6 AND measure='Operating income' THEN amount END) oh FROM financials WHERE period_end='2024-12-31') SELECT oh-o2 FROM x",
      "status": "answered",
      "unit": "usd_million",
      "value": 30552.0
    },
    {
      "evidence": [
        "a03:s02",
        "a03:s03"
      ],
      "id": "margin_change",
      "reason_code": null,
      "sql": "WITH x AS (SELECT MAX(CASE WHEN months=3 AND measure='Total revenue' THEN amount END) r2,MAX(CASE WHEN months=6 AND measure='Total revenue' THEN amount END) rh,MAX(CASE WHEN months=3 AND measure='Operating income' THEN amount END) o2,MAX(CASE WHEN months=6 AND measure='Operating income' THEN amount END) oh FROM financials WHERE period_end='2024-12-31') SELECT 10000.0*(o2/r2-(oh-o2)/(rh-r2)) FROM x",
      "status": "answered",
      "unit": "basis_points",
      "value": -112.62742667169121
    },
    {
      "evidence": [
        "a03:s01",
        "a03:s04"
      ],
      "id": "azure_gap",
      "reason_code": null,
      "sql": "SELECT (SELECT constant_currency_percent FROM growth WHERE business='Azure and other cloud services')-(SELECT high FROM guidance WHERE issue_date='2024-10-30' AND fiscal_period='Q2FY2025' AND basis='constant_currency')",
      "status": "answered",
      "unit": "percentage_points",
      "value": -1.0
    }
  ],
  "conclusion": {
    "evidence": [
      "a03:s01",
      "a03:s04"
    ],
    "reason_code": null,
    "verdict": "contradicted"
  },
  "task_id": "challenge-v1-a03"
}
ANSWER
