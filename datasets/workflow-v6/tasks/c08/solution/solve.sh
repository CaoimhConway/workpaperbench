#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/income_reconciliation.sql <<'SQL'
SELECT b.period,b.gaap_income_usd_million,SUM(a.signed_income_adjustment_usd_million) signed_adjustment_usd_million,
b.gaap_income_usd_million+SUM(a.signed_income_adjustment_usd_million) adjusted_income_usd_million,
b.gaap_income_usd_million+SUM(a.signed_income_adjustment_usd_million)-b.reported_adjusted_income_usd_million residual_usd_million
FROM income_bases b JOIN income_adjustments a ON b.period=a.period WHERE b.period IN ('Q4FY2025','Q3FY2025','Q4FY2024','FY2025','FY2024') GROUP BY b.period
SQL
cat > /logs/artifacts/share_basis.sql <<'SQL'
WITH p AS (SELECT b.*,b.gaap_income_usd_million+SUM(a.signed_income_adjustment_usd_million) adjusted FROM income_bases b
JOIN income_adjustments a ON b.period=a.period GROUP BY b.period)
SELECT period,gaap_shares_million,adjusted_shares_million,1.0*gaap_income_usd_million/gaap_shares_million computed_gaap_eps_usd,
1.0*gaap_income_usd_million/gaap_shares_million-reported_gaap_eps_usd gaap_eps_rounding_residual_usd,
1.0*adjusted/adjusted_shares_million computed_adjusted_eps_usd,1.0*adjusted/gaap_shares_million adjusted_income_over_gaap_shares_usd,
1.0*adjusted/adjusted_shares_million-1.0*adjusted/gaap_shares_million denominator_effect_usd
FROM p WHERE period IN ('Q4FY2025','Q3FY2025','Q4FY2024','FY2025','FY2024')
SQL
cat > /logs/artifacts/segment_growth_bridge.sql <<'SQL'
WITH p AS (SELECT CASE WHEN period LIKE 'Q4%' THEN 'Q4FY' ELSE 'FY' END window,period,segment,revenue_usd_million FROM segments
WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025')),totals AS (SELECT window,SUM(CASE WHEN period LIKE '%2025' THEN revenue_usd_million ELSE -revenue_usd_million END) delta FROM p GROUP BY window)
SELECT c.window,c.segment,p.revenue_usd_million prior_usd_million,c.revenue_usd_million current_usd_million,c.revenue_usd_million-p.revenue_usd_million change_usd_million,
100.0*(c.revenue_usd_million-p.revenue_usd_million)/t.delta contribution_to_total_growth_pct FROM p c JOIN p ON c.window=p.window AND c.segment=p.segment AND c.period LIKE '%2025' AND p.period LIKE '%2024' JOIN totals t ON t.window=c.window
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v6-c08",
  "tables": [
    {
      "id": "income_reconciliation",
      "file": "income_reconciliation.sql",
      "evidence": [
        "c08:s01"
      ]
    },
    {
      "id": "share_basis",
      "file": "share_basis.sql",
      "evidence": [
        "c08:s01",
        "c08:s02"
      ]
    },
    {
      "id": "segment_growth_bridge",
      "file": "segment_growth_bridge.sql",
      "evidence": [
        "c08:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "c08:s02"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "c08:s03"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "unresolved",
      "evidence": [
        "c08:s03"
      ]
    }
  ]
}
ANSWER
