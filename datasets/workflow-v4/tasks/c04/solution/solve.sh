#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/regional_attribution.sql <<'SQL'
SELECT CASE WHEN c.period='FY2025' THEN 'FY' ELSE 'Q4FY' END window,c.region,
p.purchase_usd_billion prior_purchase_usd_billion,c.purchase_usd_billion current_purchase_usd_billion,
c.purchase_usd_billion-p.purchase_usd_billion change_usd_billion,
100.0*(c.purchase_usd_billion-p.purchase_usd_billion)/(wc.purchase_usd_billion-wp.purchase_usd_billion) contribution_to_worldwide_purchase_growth_pct,
1000.0*p.purchase_usd_billion/p.purchase_transactions_million prior_average_purchase_usd,
1000.0*c.purchase_usd_billion/c.purchase_transactions_million current_average_purchase_usd,
100.0*((c.purchase_usd_billion/c.purchase_transactions_million)/(p.purchase_usd_billion/p.purchase_transactions_million)-1) average_purchase_growth_pct,
c.purchase_usd_billion+c.cash_usd_billion-c.gdv_usd_billion current_gdv_residual_usd_billion
FROM regions c JOIN regions p ON c.region=p.region AND ((c.period='FY2025' AND p.period='FY2024') OR (c.period='Q4FY2025' AND p.period='Q4FY2024'))
JOIN worldwide wc ON wc.period=c.period JOIN worldwide wp ON wp.period=p.period
SQL
cat > /logs/artifacts/worldwide_reconciliation.sql <<'SQL'
WITH p AS (SELECT period,SUM(gdv_usd_billion) g,SUM(purchase_usd_billion) v,SUM(purchase_transactions_million) n
FROM regions WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025') GROUP BY period)
SELECT p.period,g regional_gdv_usd_billion,v regional_purchase_usd_billion,n regional_purchase_transactions_million,
g-w.gdv_usd_billion gdv_residual_usd_billion,v-w.purchase_usd_billion purchase_residual_usd_billion,
n-w.purchase_transactions_million transaction_residual_million FROM p JOIN worldwide w USING(period)
SQL
cat > /logs/artifacts/company_margin_bridge.sql <<'SQL'
SELECT period,revenue_usd_million-gaap_expense_usd_million gaap_operating_income_usd_million,
revenue_usd_million-adjusted_expense_usd_million adjusted_operating_income_usd_million,
100.0*(revenue_usd_million-gaap_expense_usd_million)/revenue_usd_million gaap_margin_pct,
100.0*(revenue_usd_million-adjusted_expense_usd_million)/revenue_usd_million adjusted_margin_pct,
gaap_expense_usd_million-litigation_usd_million-restructuring_usd_million-adjusted_expense_usd_million expense_residual_usd_million
FROM financials WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025')
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v4-c04",
  "tables": [
    {
      "id": "regional_attribution",
      "file": "regional_attribution.sql",
      "evidence": [
        "c04:s01",
        "c04:s02"
      ]
    },
    {
      "id": "worldwide_reconciliation",
      "file": "worldwide_reconciliation.sql",
      "evidence": [
        "c04:s01"
      ]
    },
    {
      "id": "company_margin_bridge",
      "file": "company_margin_bridge.sql",
      "evidence": [
        "c04:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "branded_volume_matches_all_revenue",
      "verdict": "contradicted",
      "evidence": [
        "c04:s02",
        "c04:s03"
      ]
    },
    {
      "id": "annual_average_purchase_increased",
      "verdict": "supported",
      "evidence": [
        "c04:s01",
        "c04:s02"
      ]
    },
    {
      "id": "merchant_price_mix_identified",
      "verdict": "unresolved",
      "evidence": [
        "c04:s02"
      ]
    }
  ]
}
ANSWER
