#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/quarter_model.sql <<'SQL'
WITH periods AS (
 SELECT period_end, MAX(CASE WHEN months=3 AND measure='Total revenue' THEN amount END) r2,
 MAX(CASE WHEN months=6 AND measure='Total revenue' THEN amount END) rh,
 MAX(CASE WHEN months=3 AND measure='Operating income' THEN amount END) o2,
 MAX(CASE WHEN months=6 AND measure='Operating income' THEN amount END) oh
 FROM financials WHERE period_end IN ('2023-12-31','2024-12-31') GROUP BY period_end
), quarters AS (
 SELECT CAST(substr(period_end,1,4) AS INTEGER)+1 fiscal_year,1 quarter,rh-r2 revenue,oh-o2 income FROM periods
 UNION ALL SELECT CAST(substr(period_end,1,4) AS INTEGER)+1,2,r2,o2 FROM periods
) SELECT fiscal_year,quarter,revenue revenue_usd_million,income operating_income_usd_million,
100.0*income/revenue operating_margin_pct FROM quarters
SQL
cat > /logs/artifacts/quarter_reconciliation.sql <<'SQL'
SELECT "fiscal_year", "margin_qoq_bps" FROM (
WITH p AS (
 SELECT period_end,MAX(CASE WHEN months=3 AND measure='Total revenue' THEN amount END) r2,
 MAX(CASE WHEN months=6 AND measure='Total revenue' THEN amount END) rh,
 MAX(CASE WHEN months=3 AND measure='Operating income' THEN amount END) o2,
 MAX(CASE WHEN months=6 AND measure='Operating income' THEN amount END) oh
 FROM financials WHERE period_end IN ('2023-12-31','2024-12-31') GROUP BY period_end
) SELECT CAST(substr(period_end,1,4) AS INTEGER)+1 fiscal_year,
(rh-r2)+r2-rh revenue_residual_usd_million,(oh-o2)+o2-oh operating_income_residual_usd_million,
10000.0*(o2/r2-(oh-o2)/(rh-r2)) margin_qoq_bps FROM p
) AS workpaper
SQL
cat > /logs/artifacts/guidance_bridge.sql <<'SQL'
SELECT a.business, a.constant_currency_percent actual_cc_pct,g.low guidance_low_pct,
g.high guidance_high_pct,a.constant_currency_percent-(g.low+g.high)/2.0 midpoint_gap_pp
FROM growth a JOIN guidance g ON a.business=g.business WHERE g.issue_date='2024-10-30'
AND g.fiscal_period='Q2FY2025' AND g.basis='constant_currency'
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v12-a01",
  "tables": [
    {
      "id": "quarter_model",
      "file": "quarter_model.sql",
      "evidence": [
        "a03:s02",
        "a03:s03"
      ]
    },
    {
      "id": "quarter_reconciliation",
      "file": "quarter_reconciliation.sql",
      "evidence": [
        "a03:s02",
        "a03:s03"
      ]
    },
    {
      "id": "guidance_bridge",
      "file": "guidance_bridge.sql",
      "evidence": [
        "a03:s01",
        "a03:s04"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "a03:s02",
        "a03:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "a03:s05"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "a03:s01",
        "a03:s04"
      ]
    }
  ]
}
ANSWER
