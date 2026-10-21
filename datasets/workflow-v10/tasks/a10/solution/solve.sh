#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/income_model.sql <<'SQL'
WITH p AS (SELECT *,discount_usd_million+card_fees_usd_million+service_other_usd_million+net_interest_usd_million computed FROM income
WHERE period IN ('Q4FY2025','Q3FY2025','Q2FY2025','Q1FY2025','Q4FY2024','FY2025','FY2024')) SELECT period,computed revenue_usd_million,
computed-provisions_usd_million-expense_usd_million pretax_usd_million,computed-provisions_usd_million-expense_usd_million-tax_usd_million net_income_usd_million,
computed-revenue_usd_million revenue_residual_usd_million,computed-provisions_usd_million-expense_usd_million-tax_usd_million-net_income_usd_million net_residual_usd_million FROM p
SQL
cat > /logs/artifacts/currency_and_network.sql <<'SQL'
SELECT window,100.0*(current_billed_usd_billion/prior_billed_usd_billion-1) billed_reported_growth_pct,
100.0*(current_billed_usd_billion/fx_prior_billed_usd_billion-1) billed_fx_growth_pct,100.0*(current_revenue_usd_million/prior_revenue_usd_million-1) revenue_reported_growth_pct,
100.0*(current_revenue_usd_million/fx_prior_revenue_usd_million-1) revenue_fx_growth_pct,current_network_usd_billion-current_billed_usd_billion current_processed_usd_billion,
prior_network_usd_billion-prior_billed_usd_billion prior_processed_usd_billion FROM comparison WHERE window IN ('FY','Q4')
SQL
cat > /logs/artifacts/revenue_growth_bridge.sql <<'SQL'
WITH p AS (SELECT period,'discount' measure,discount_usd_million amount FROM income UNION ALL SELECT period,'card_fees',card_fees_usd_million FROM income
UNION ALL SELECT period,'service_other',service_other_usd_million FROM income UNION ALL SELECT period,'net_interest',net_interest_usd_million FROM income)
SELECT g.window,c.measure,c.amount-p.amount change_usd_million,100.0*(c.amount-p.amount)/(g.current_revenue_usd_million-g.prior_revenue_usd_million) contribution_to_revenue_growth_pct
FROM comparison g JOIN p c ON c.period=(CASE g.window WHEN 'Q4' THEN 'Q4FY' ELSE 'FY' END)||'2025' JOIN p ON p.period=(CASE g.window WHEN 'Q4' THEN 'Q4FY' ELSE 'FY' END)||'2024' AND p.measure=c.measure WHERE g.window IN ('FY','Q4')
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v10-a10",
  "tables": [
    {
      "id": "income_model",
      "file": "income_model.sql",
      "evidence": [
        "a10:s01"
      ]
    },
    {
      "id": "currency_and_network",
      "file": "currency_and_network.sql",
      "evidence": [
        "a10:s02",
        "a10:s03"
      ]
    },
    {
      "id": "revenue_growth_bridge",
      "file": "revenue_growth_bridge.sql",
      "evidence": [
        "a10:s01",
        "a10:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "supported",
      "evidence": [
        "a10:s01",
        "a10:s02"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "a10:s02",
        "a10:s03"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "a10:s02"
      ]
    }
  ]
}
ANSWER
