#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/geographic_currency.sql <<'SQL'
SELECT comparison,region,prior_usd_million,current_usd_million,fx_effect_usd_million,current_usd_million-fx_effect_usd_million cc_current_usd_million,
100.0*(current_usd_million/prior_usd_million-1) reported_growth_pct,
100.0*((current_usd_million-fx_effect_usd_million)/prior_usd_million-1) cc_growth_pct FROM geography WHERE comparison IN ('year_over_year','quarter_over_quarter')
SQL
cat > /logs/artifacts/consolidated_currency_bridge.sql <<'SQL'
SELECT "comparison", "prior_reported_usd_million", "current_reported_usd_million", "cc_current_usd_million", "cc_change_usd_million", "fx_effect_usd_million", "hedging_change_usd_million", "reported_change_usd_million", "cc_growth_pct", "cc_disclosure_residual_usd_million" FROM (
WITH g AS (SELECT comparison,SUM(prior_usd_million) p,SUM(current_usd_million) c,SUM(fx_effect_usd_million) f FROM geography GROUP BY comparison)
SELECT g.comparison,p+h.prior_usd_million prior_reported_usd_million,c+h.current_usd_million current_reported_usd_million,
c-f cc_current_usd_million,c-f-p cc_change_usd_million,f fx_effect_usd_million,h.current_usd_million-h.prior_usd_million hedging_change_usd_million,
c+h.current_usd_million-p-h.prior_usd_million reported_change_usd_million,
(c-f-p)+f+(h.current_usd_million-h.prior_usd_million)-(c+h.current_usd_million-p-h.prior_usd_million) bridge_residual_usd_million,
100.0*((c-f)/p-1) cc_growth_pct,c-f-h.reported_cc_usd_million cc_disclosure_residual_usd_million FROM g JOIN hedging h ON g.comparison=h.comparison
WHERE g.comparison IN ('year_over_year','quarter_over_quarter')
) AS workpaper
SQL
cat > /logs/artifacts/revenue_growth_components.sql <<'SQL'
WITH total AS (SELECT SUM(CASE WHEN year=2025 THEN revenue_usd_million WHEN year=2024 THEN -revenue_usd_million ELSE 0 END) delta FROM revenue_components)
SELECT c.measure,p.revenue_usd_million prior_usd_million,c.revenue_usd_million current_usd_million,c.revenue_usd_million-p.revenue_usd_million change_usd_million,
100.0*(c.revenue_usd_million-p.revenue_usd_million)/total.delta contribution_to_reported_growth_pct FROM revenue_components c
JOIN revenue_components p ON p.measure=c.measure AND p.year=2024 AND c.year=2025 CROSS JOIN total
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v9-c06",
  "tables": [
    {
      "id": "geographic_currency",
      "file": "geographic_currency.sql",
      "evidence": [
        "c06:s01"
      ]
    },
    {
      "id": "consolidated_currency_bridge",
      "file": "consolidated_currency_bridge.sql",
      "evidence": [
        "c06:s01"
      ]
    },
    {
      "id": "revenue_growth_components",
      "file": "revenue_growth_components.sql",
      "evidence": [
        "c06:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "supported",
      "evidence": [
        "c06:s01"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "c06:s02"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "c06:s02"
      ]
    }
  ]
}
ANSWER
