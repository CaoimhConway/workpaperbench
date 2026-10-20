#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/operating_reconciliation.sql <<'SQL'
SELECT b.fiscal_year,b.window,b.gaap_operating_usd_million,SUM(a.signed_adjustment_usd_million) signed_exclusion_usd_million,
b.gaap_operating_usd_million+SUM(a.signed_adjustment_usd_million) adjusted_operating_usd_million,
b.gaap_operating_usd_million+SUM(a.signed_adjustment_usd_million)-b.reported_adjusted_operating_usd_million residual_usd_million
FROM income_bases b JOIN adjustments a USING(fiscal_year,window) WHERE b.fiscal_year IN (2024,2025) AND b.window IN ('Q1','Q2','Q3','Q4','FY')
AND a.scope='operating_and_income' GROUP BY b.fiscal_year,b.window
SQL
cat > /logs/artifacts/income_reconciliation.sql <<'SQL'
SELECT b.fiscal_year,b.window,b.gaap_income_usd_million,SUM(a.signed_adjustment_usd_million) signed_exclusion_usd_million,
b.gaap_income_usd_million+SUM(a.signed_adjustment_usd_million) adjusted_income_usd_million,
b.gaap_income_usd_million+SUM(a.signed_adjustment_usd_million)-b.reported_adjusted_income_usd_million residual_usd_million
FROM income_bases b JOIN adjustments a USING(fiscal_year,window) WHERE b.fiscal_year IN (2024,2025) AND b.window IN ('Q1','Q2','Q3','Q4','FY') GROUP BY b.fiscal_year,b.window
SQL
cat > /logs/artifacts/share_basis.sql <<'SQL'
WITH p AS (SELECT b.*,b.gaap_income_usd_million+SUM(a.signed_adjustment_usd_million) adjusted FROM income_bases b JOIN adjustments a USING(fiscal_year,window)
GROUP BY b.fiscal_year,b.window) SELECT fiscal_year,window,gaap_shares_million,adjusted_shares_million,
1.0*gaap_income_usd_million/gaap_shares_million computed_gaap_eps_usd,1.0*adjusted/adjusted_shares_million computed_adjusted_eps_usd,
1.0*adjusted/gaap_shares_million adjusted_income_over_gaap_shares_usd,1.0*adjusted/adjusted_shares_million-1.0*adjusted/gaap_shares_million denominator_effect_usd
FROM p WHERE fiscal_year IN (2024,2025) AND window IN ('Q1','Q2','Q3','Q4','FY')
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v9-b09",
  "tables": [
    {
      "id": "operating_reconciliation",
      "file": "operating_reconciliation.sql",
      "evidence": [
        "b09:s01",
        "b09:s02"
      ]
    },
    {
      "id": "income_reconciliation",
      "file": "income_reconciliation.sql",
      "evidence": [
        "b09:s01",
        "b09:s02"
      ]
    },
    {
      "id": "share_basis",
      "file": "share_basis.sql",
      "evidence": [
        "b09:s01",
        "b09:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "supported",
      "evidence": [
        "b09:s01",
        "b09:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "b09:s01"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "b09:s02"
      ]
    }
  ]
}
ANSWER
