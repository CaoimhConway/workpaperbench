#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/expense_audit.sql <<'SQL'
SELECT period,gaap_expense_usd_million,
gaap_expense_usd_million-sbc_usd_million-settlement_expense_usd_million-credit_loss_exclusion_usd_million adjusted_expense_usd_million,
gaap_expense_usd_million-settlement_expense_usd_million-credit_loss_exclusion_usd_million adjusted_including_sbc_usd_million,
-settlement_expense_usd_million removal_of_settlement_usd_million,
gaap_expense_usd_million-sbc_usd_million-settlement_expense_usd_million-credit_loss_exclusion_usd_million-adjusted_expense_usd_million residual_usd_million,
gaap_expense_usd_million-sbc_usd_million-settlement_expense_usd_million-credit_loss_provision_usd_million comparable_credit_excluded_expense_usd_million
FROM expenses WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025','Q3FY2025')
SQL
cat > /logs/artifacts/annual_revenue_bridge.sql <<'SQL'
WITH p AS (SELECT * FROM revenues WHERE period='FY2024'),c AS (SELECT * FROM revenues WHERE period='FY2025'),
components AS (SELECT 'transaction' measure,p.transaction_usd_million prior,c.transaction_usd_million current FROM p CROSS JOIN c
UNION ALL SELECT 'interest',p.interest_usd_million,c.interest_usd_million FROM p CROSS JOIN c
UNION ALL SELECT 'other',p.other_usd_million,c.other_usd_million FROM p CROSS JOIN c)
SELECT measure,prior prior_usd_million,current current_usd_million,current-prior change_usd_million,
100.0*(current-prior)/(c.total_usd_million-p.total_usd_million) contribution_to_total_growth_pct FROM components CROSS JOIN p CROSS JOIN c
SQL
cat > /logs/artifacts/crypto_scope.sql <<'SQL'
SELECT s.period,s.scope,CAST(s.months AS INTEGER) months,s.volume_usd_billion,
100.0*s.volume_usd_billion/t.volume_usd_billion share_of_combined_pct,
1.0*s.volume_usd_billion/s.months monthly_average_usd_billion FROM crypto_volumes s JOIN crypto_volumes t ON t.period=s.period AND t.scope='total'
WHERE s.period IN ('Q4FY2025','January2026') AND s.scope IN ('app','bitstamp')
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v13-b04",
  "tables": [
    {
      "id": "expense_audit",
      "file": "expense_audit.sql",
      "evidence": [
        "b04:s01"
      ]
    },
    {
      "id": "annual_revenue_bridge",
      "file": "annual_revenue_bridge.sql",
      "evidence": [
        "b04:s01"
      ]
    },
    {
      "id": "crypto_scope",
      "file": "crypto_scope.sql",
      "evidence": [
        "b04:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "unresolved",
      "evidence": [
        "b04:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "b04:s01"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "b04:s02"
      ]
    }
  ]
}
ANSWER
