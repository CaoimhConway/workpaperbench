#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/quarter_activity.sql <<'SQL'
SELECT period,active_accounts_million,transactions_million,
1.0*transactions_million/active_accounts_million quarter_transactions_per_active_account,reported_ttm_activity
FROM quarters WHERE period IN ('Q4FY2024','Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025')
SQL
cat > /logs/artifacts/margin_reconciliation.sql <<'SQL'
WITH p AS (SELECT *,net_revenue_usd_million-transaction_expense_usd_million-losses_usd_million tm FROM margin
WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025'))
SELECT period,tm transaction_margin_usd_million,tm-customer_interest_usd_million tm_ex_interest_usd_million,
100.0*tm/net_revenue_usd_million tm_margin_pct,100.0*(tm-customer_interest_usd_million)/net_revenue_usd_million tm_ex_interest_margin_pct,
tm-reported_tm_usd_million tm_residual_usd_million,tm-customer_interest_usd_million-reported_tm_ex_interest_usd_million ex_interest_residual_usd_million FROM p
SQL
cat > /logs/artifacts/annual_activity_bridge.sql <<'SQL'
WITH annual AS (SELECT SUM(transactions_million) t,SUM(transaction_revenue_usd_million) r,
SUM(ovas_usd_million) o,SUM(net_revenue_usd_million) n,SUM(tpv_usd_million) v FROM quarters
WHERE period IN ('Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025'))
SELECT 'FY2025' period,t transactions_million,1.0*t/q.active_accounts_million recomputed_ttm_activity,
1.0*t/q.active_accounts_million-q.reported_ttm_activity rounded_activity_residual,r transaction_revenue_usd_million,
o ovas_usd_million,n net_revenue_usd_million,r+o-n revenue_residual_usd_million,v tpv_usd_million,100.0*r/v transaction_revenue_to_tpv_pct
FROM annual JOIN quarters q ON q.period='Q4FY2025'
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v12-b05",
  "tables": [
    {
      "id": "quarter_activity",
      "file": "quarter_activity.sql",
      "evidence": [
        "b05:s01",
        "b05:s02"
      ]
    },
    {
      "id": "margin_reconciliation",
      "file": "margin_reconciliation.sql",
      "evidence": [
        "b05:s03"
      ]
    },
    {
      "id": "annual_activity_bridge",
      "file": "annual_activity_bridge.sql",
      "evidence": [
        "b05:s01",
        "b05:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "supported",
      "evidence": [
        "b05:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "b05:s01"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "b05:s01",
        "b05:s02"
      ]
    }
  ]
}
ANSWER
