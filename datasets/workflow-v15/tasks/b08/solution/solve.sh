#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/category_economics.sql <<'SQL'
WITH p AS (SELECT * FROM periods WHERE year IN (2024,2025)
UNION ALL SELECT a.year,9,a.gmv_usd_million-q.gmv_usd_million,a.subscription_revenue_usd_million-q.subscription_revenue_usd_million,
a.merchant_revenue_usd_million-q.merchant_revenue_usd_million,a.subscription_cost_usd_million-q.subscription_cost_usd_million,
a.merchant_cost_usd_million-q.merchant_cost_usd_million,a.operating_expense_usd_million-q.operating_expense_usd_million,
a.reported_operating_income_usd_million-q.reported_operating_income_usd_million,a.operating_cash_usd_million-q.operating_cash_usd_million,
a.capex_usd_million-q.capex_usd_million,a.reported_fcf_usd_million-q.reported_fcf_usd_million
FROM periods a JOIN periods q ON a.year=q.year AND a.months=12 AND q.months=3 WHERE a.year IN (2024,2025)) SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,
subscription_revenue_usd_million-subscription_cost_usd_million subscription_gp_usd_million,
merchant_revenue_usd_million-merchant_cost_usd_million merchant_gp_usd_million,
100.0*(subscription_revenue_usd_million-subscription_cost_usd_million)/subscription_revenue_usd_million subscription_margin_pct,
100.0*(merchant_revenue_usd_million-merchant_cost_usd_million)/merchant_revenue_usd_million merchant_margin_pct,
subscription_revenue_usd_million+merchant_revenue_usd_million-subscription_cost_usd_million-merchant_cost_usd_million-operating_expense_usd_million operating_income_usd_million,
subscription_revenue_usd_million+merchant_revenue_usd_million-subscription_cost_usd_million-merchant_cost_usd_million-operating_expense_usd_million-reported_operating_income_usd_million residual_usd_million,
100.0*merchant_revenue_usd_million/gmv_usd_million merchant_revenue_to_gmv_pct FROM p
SQL
cat > /logs/artifacts/cash_generation.sql <<'SQL'
WITH p AS (SELECT * FROM periods WHERE year IN (2024,2025)
UNION ALL SELECT a.year,9,a.gmv_usd_million-q.gmv_usd_million,a.subscription_revenue_usd_million-q.subscription_revenue_usd_million,
a.merchant_revenue_usd_million-q.merchant_revenue_usd_million,a.subscription_cost_usd_million-q.subscription_cost_usd_million,
a.merchant_cost_usd_million-q.merchant_cost_usd_million,a.operating_expense_usd_million-q.operating_expense_usd_million,
a.reported_operating_income_usd_million-q.reported_operating_income_usd_million,a.operating_cash_usd_million-q.operating_cash_usd_million,
a.capex_usd_million-q.capex_usd_million,a.reported_fcf_usd_million-q.reported_fcf_usd_million
FROM periods a JOIN periods q ON a.year=q.year AND a.months=12 AND q.months=3 WHERE a.year IN (2024,2025)) SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,
subscription_revenue_usd_million+merchant_revenue_usd_million revenue_usd_million,operating_cash_usd_million-capex_usd_million fcf_usd_million,
100.0*(operating_cash_usd_million-capex_usd_million)/(subscription_revenue_usd_million+merchant_revenue_usd_million) fcf_margin_pct,
operating_cash_usd_million-capex_usd_million-reported_fcf_usd_million residual_usd_million FROM p
SQL
cat > /logs/artifacts/subscription_stock_bridge.sql <<'SQL'
SELECT CAST(s.year AS INTEGER) year,s.mrr_usd_million,12.0*s.mrr_usd_million exit_annual_run_rate_usd_million,
p.subscription_revenue_usd_million observed_annual_subscription_revenue_usd_million,
12.0*s.mrr_usd_million-p.subscription_revenue_usd_million run_rate_minus_observed_usd_million,
100.0*(12.0*s.mrr_usd_million/p.subscription_revenue_usd_million-1) run_rate_gap_pct
FROM subscription_stocks s JOIN periods p ON s.year=p.year AND p.months=12 WHERE s.year IN (2024,2025)
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v15-b08",
  "tables": [
    {
      "id": "category_economics",
      "file": "category_economics.sql",
      "evidence": [
        "b08:s01"
      ]
    },
    {
      "id": "cash_generation",
      "file": "cash_generation.sql",
      "evidence": [
        "b08:s01",
        "b08:s03"
      ]
    },
    {
      "id": "subscription_stock_bridge",
      "file": "subscription_stock_bridge.sql",
      "evidence": [
        "b08:s02",
        "b08:s01"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "b08:s02",
        "b08:s01"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "b08:s01"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "b08:s01"
      ]
    }
  ]
}
ANSWER
