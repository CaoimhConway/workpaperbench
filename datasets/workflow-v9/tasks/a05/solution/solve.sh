#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/income_model.sql <<'SQL'
WITH periods AS (SELECT * FROM income WHERE fiscal_year IN (2024,2025) UNION ALL
SELECT a.fiscal_year,36,a.net_sales_usd_million-q.net_sales_usd_million,a.membership_usd_million-q.membership_usd_million,
a.revenue_usd_million-q.revenue_usd_million,a.merchandise_cost_usd_million-q.merchandise_cost_usd_million,
a.sga_usd_million-q.sga_usd_million,a.operating_income_usd_million-q.operating_income_usd_million
FROM income a JOIN income q ON a.fiscal_year=q.fiscal_year AND a.weeks=52 AND q.weeks=16 WHERE a.fiscal_year IN (2024,2025)) SELECT fiscal_year,weeks,net_sales_usd_million,membership_usd_million,
net_sales_usd_million-merchandise_cost_usd_million merchandise_gross_profit_usd_million,
100.0*(net_sales_usd_million-merchandise_cost_usd_million)/net_sales_usd_million merchandise_gross_margin_pct,
net_sales_usd_million-merchandise_cost_usd_million+membership_usd_million-sga_usd_million operating_income_usd_million,
net_sales_usd_million-merchandise_cost_usd_million+membership_usd_million-sga_usd_million-operating_income_usd_million residual_usd_million FROM periods
SQL
cat > /logs/artifacts/operating_growth_bridge.sql <<'SQL'
WITH periods AS (SELECT * FROM income WHERE fiscal_year IN (2024,2025) UNION ALL
SELECT a.fiscal_year,36,a.net_sales_usd_million-q.net_sales_usd_million,a.membership_usd_million-q.membership_usd_million,
a.revenue_usd_million-q.revenue_usd_million,a.merchandise_cost_usd_million-q.merchandise_cost_usd_million,
a.sga_usd_million-q.sga_usd_million,a.operating_income_usd_million-q.operating_income_usd_million
FROM income a JOIN income q ON a.fiscal_year=q.fiscal_year AND a.weeks=52 AND q.weeks=16 WHERE a.fiscal_year IN (2024,2025)) ,components AS (
SELECT fiscal_year,weeks,'merchandise_gross_profit' measure,net_sales_usd_million-merchandise_cost_usd_million amount FROM periods
UNION ALL SELECT fiscal_year,weeks,'membership_fees',membership_usd_million FROM periods
UNION ALL SELECT fiscal_year,weeks,'sga',-sga_usd_million FROM periods)
SELECT c.weeks,c.measure,p.amount prior_usd_million,c.amount current_usd_million,c.amount-p.amount change_usd_million,
100.0*(c.amount-p.amount)/(ct.operating_income_usd_million-pt.operating_income_usd_million) contribution_to_operating_growth_pct
FROM components c JOIN components p ON c.fiscal_year=2025 AND p.fiscal_year=2024 AND c.weeks=p.weeks AND c.measure=p.measure
JOIN periods ct ON ct.fiscal_year=2025 AND ct.weeks=c.weeks JOIN periods pt ON pt.fiscal_year=2024 AND pt.weeks=c.weeks
SQL
cat > /logs/artifacts/membership_accrual_bridge.sql <<'SQL'
SELECT 'FY2025' period,i.membership_usd_million earned_fees_usd_million,p.amount_usd_million opening_deferred_usd_million,
c.amount_usd_million closing_deferred_usd_million,c.amount_usd_million-p.amount_usd_million deferred_change_usd_million,
i.membership_usd_million+c.amount_usd_million-p.amount_usd_million mechanical_accrual_bridge_usd_million
FROM income i JOIN deferred_membership p ON p.economic_date='2024-09-01' JOIN deferred_membership c ON c.economic_date='2025-08-31'
WHERE i.fiscal_year=2025 AND i.weeks=52
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v9-a05",
  "tables": [
    {
      "id": "income_model",
      "file": "income_model.sql",
      "evidence": [
        "a05:s01"
      ]
    },
    {
      "id": "operating_growth_bridge",
      "file": "operating_growth_bridge.sql",
      "evidence": [
        "a05:s01"
      ]
    },
    {
      "id": "membership_accrual_bridge",
      "file": "membership_accrual_bridge.sql",
      "evidence": [
        "a05:s01",
        "a05:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "supported",
      "evidence": [
        "a05:s01"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "a05:s01"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "a05:s01"
      ]
    }
  ]
}
ANSWER
