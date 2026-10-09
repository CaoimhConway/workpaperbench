#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/operating_reconciliation.sql <<'SQL'
WITH p AS (SELECT period,
MAX(CASE WHEN measure='gaap_operating_income' THEN amount END) gaap,
MAX(CASE WHEN measure='non_gaap_operating_income' THEN amount END) adjusted,
SUM(CASE WHEN measure NOT IN ('gaap_operating_income','non_gaap_operating_income') THEN amount ELSE 0 END) gap
FROM operating_reconciliation WHERE period IN ('FY2024','FY2025','Q4FY2024','Q3FY2025','Q4FY2025') GROUP BY period)
SELECT period,gaap gaap_operating_income_usd_million,gap adjustments_usd_million,
adjusted adjusted_operating_income_usd_million,gaap+gap-adjusted residual_usd_million FROM p
SQL
cat > /logs/artifacts/adjustment_attribution.sql <<'SQL'
WITH p AS (SELECT measure,
MAX(CASE WHEN period='FY2024' THEN amount END) prior,
MAX(CASE WHEN period='FY2025' THEN amount END) current
FROM operating_reconciliation WHERE period IN ('FY2024','FY2025') GROUP BY measure),
t AS (SELECT (SELECT current-prior FROM p WHERE measure='non_gaap_operating_income')-
(SELECT current-prior FROM p WHERE measure='gaap_operating_income') gap_delta)
SELECT measure,prior prior_usd_million,current current_usd_million,current-prior change_usd_million,
100.0*(current-prior)/t.gap_delta contribution_to_gap_change_pct FROM p CROSS JOIN t
WHERE measure NOT IN ('gaap_operating_income','non_gaap_operating_income')
SQL
cat > /logs/artifacts/arr_guidance_bridge.sql <<'SQL'
SELECT 'FY2026' fiscal_year,p.amount_usd_billion observed_exit_arr_usd_billion,
c.amount_usd_billion revalued_opening_arr_usd_billion,
1000.0*(c.amount_usd_billion-p.amount_usd_billion) revaluation_usd_million,
t.value target_arr_growth_pct,c.amount_usd_billion*(1+t.value/100.0) implied_target_arr_usd_billion
FROM arr_basis p CROSS JOIN arr_basis c JOIN targets t ON t.period='FY2026' AND t.measure='ending_arr_growth_pct'
WHERE p.basis='FY2025_exit' AND c.basis='FY2026_opening_revalued'
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v2-c02",
  "tables": [
    {
      "id": "operating_reconciliation",
      "file": "operating_reconciliation.sql",
      "evidence": [
        "c02:s01"
      ]
    },
    {
      "id": "adjustment_attribution",
      "file": "adjustment_attribution.sql",
      "evidence": [
        "c02:s01"
      ]
    },
    {
      "id": "arr_guidance_bridge",
      "file": "arr_guidance_bridge.sql",
      "evidence": [
        "c02:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "adjusted_growth_slower_than_gaap",
      "verdict": "supported",
      "evidence": [
        "c02:s01"
      ]
    },
    {
      "id": "arr_revaluation_is_recognized_revenue",
      "verdict": "contradicted",
      "evidence": [
        "c02:s02",
        "c02:s03"
      ]
    },
    {
      "id": "exact_organic_arr_increase_identifiable",
      "verdict": "unresolved",
      "evidence": [
        "c02:s02"
      ]
    }
  ]
}
ANSWER
