#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/expense_model.sql <<'SQL'
WITH p AS (SELECT period,
MAX(CASE WHEN measure='gaap' THEN amount_usd_thousand END) g,
SUM(CASE WHEN group_name='prior_adjustment' THEN amount_usd_thousand ELSE 0 END) a,
SUM(CASE WHEN group_name='extra_adjustment' THEN amount_usd_thousand ELSE 0 END) e,
MAX(CASE WHEN measure='prior_definition' THEN amount_usd_thousand END) old,
MAX(CASE WHEN measure='new_definition' THEN amount_usd_thousand END) new
FROM expense_reconciliation WHERE period IN ('FY2024','FY2025','Q4FY2024','Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025') GROUP BY period),
all_periods AS (SELECT * FROM p UNION ALL SELECT '9M'||a.period,a.g-q.g,a.a-q.a,a.e-q.e,a.old-q.old,a.new-q.new
FROM p a JOIN p q ON q.period='Q4'||a.period WHERE a.period IN ('FY2024','FY2025'))
SELECT period,g gaap_expense_usd_thousand,g+a prior_adjusted_usd_thousand,g+a+e new_adjusted_usd_thousand,
-e additional_exclusions_usd_thousand,g+a-old prior_residual_usd_thousand,g+a+e-new new_residual_usd_thousand FROM all_periods
SQL
cat > /logs/artifacts/operating_margins.sql <<'SQL'
WITH p AS (SELECT period,
SUM(CASE WHEN measure IN ('reserve_income','other_revenue') THEN amount_usd_thousand ELSE 0 END) r,
SUM(CASE WHEN measure IN ('distribution','other_costs') THEN amount_usd_thousand ELSE 0 END) c,
MAX(CASE WHEN measure='total_revenue' THEN amount_usd_thousand END) reported_r,
MAX(CASE WHEN measure='total_costs' THEN amount_usd_thousand END) reported_c,
MAX(CASE WHEN measure='adjusted_ebitda' THEN amount_usd_thousand END) e
FROM operations WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025') GROUP BY period)
SELECT period,r revenue_usd_thousand,r-c rldc_usd_thousand,100.0*(r-c)/r rldc_margin_pct,
100.0*e/(r-c) adjusted_ebitda_margin_pct,r-reported_r revenue_residual_usd_thousand,c-reported_c cost_residual_usd_thousand FROM p
SQL
cat > /logs/artifacts/definition_attribution.sql <<'SQL'
WITH components AS (SELECT measure,
-MAX(CASE WHEN period='FY2024' THEN amount_usd_thousand END) p,
-MAX(CASE WHEN period='FY2025' THEN amount_usd_thousand END) c FROM expense_reconciliation
WHERE group_name='extra_adjustment' AND period IN ('FY2024','FY2025') GROUP BY measure),
delta AS (SELECT SUM(c-p) total FROM components)
SELECT measure,p prior_usd_thousand,c current_usd_thousand,c-p change_usd_thousand,
100.0*(c-p)/total contribution_to_definition_gap_change_pct FROM components CROSS JOIN delta
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v12-a03",
  "tables": [
    {
      "id": "expense_model",
      "file": "expense_model.sql",
      "evidence": [
        "a03:s01"
      ]
    },
    {
      "id": "operating_margins",
      "file": "operating_margins.sql",
      "evidence": [
        "a03:s02",
        "a03:s03"
      ]
    },
    {
      "id": "definition_attribution",
      "file": "definition_attribution.sql",
      "evidence": [
        "a03:s01"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "supported",
      "evidence": [
        "a03:s01"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "unresolved",
      "evidence": [
        "a03:s02",
        "a03:s03"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "a03:s03"
      ]
    }
  ]
}
ANSWER
