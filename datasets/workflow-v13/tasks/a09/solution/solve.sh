#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/segment_model.sql <<'SQL'
WITH p AS (SELECT * FROM segments WHERE fiscal_year IN (2024,2025)),periods AS (SELECT * FROM p UNION ALL
SELECT a.fiscal_year,9,a.segment,a.revenue_usd_million-q.revenue_usd_million,a.operating_income_usd_million-q.operating_income_usd_million
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.segment=q.segment AND a.months=12 AND q.months=3) SELECT fiscal_year,months,segment,revenue_usd_million,operating_income_usd_million,100.0*operating_income_usd_million/revenue_usd_million margin_pct FROM periods
SQL
cat > /logs/artifacts/consolidated_bridge.sql <<'SQL'
WITH p AS (SELECT * FROM segments WHERE fiscal_year IN (2024,2025)),periods AS (SELECT * FROM p UNION ALL
SELECT a.fiscal_year,9,a.segment,a.revenue_usd_million-q.revenue_usd_million,a.operating_income_usd_million-q.operating_income_usd_million
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.segment=q.segment AND a.months=12 AND q.months=3) ,r AS (SELECT * FROM reconciliation WHERE fiscal_year IN (2024,2025)),recons AS (SELECT * FROM r UNION ALL SELECT a.fiscal_year,9,
a.pretax_income_usd_million-q.pretax_income_usd_million,a.corporate_usd_million-q.corporate_usd_million,a.india_loss_usd_million-q.india_loss_usd_million,
a.restructuring_usd_million-q.restructuring_usd_million,a.other_expense_usd_million-q.other_expense_usd_million,a.interest_usd_million-q.interest_usd_million,
a.amortization_usd_million-q.amortization_usd_million,a.reported_segment_operating_usd_million-q.reported_segment_operating_usd_million,
a.revenue_eliminations_usd_million-q.revenue_eliminations_usd_million FROM r a JOIN r q ON a.fiscal_year=q.fiscal_year AND a.months=12 AND q.months=3)
SELECT p.fiscal_year,p.months,SUM(p.revenue_usd_million) gross_segment_revenue_usd_million,r.revenue_eliminations_usd_million,
SUM(p.revenue_usd_million)+r.revenue_eliminations_usd_million consolidated_revenue_usd_million,SUM(p.operating_income_usd_million) segment_operating_usd_million,
r.pretax_income_usd_million,r.corporate_usd_million+r.india_loss_usd_million+r.restructuring_usd_million+r.other_expense_usd_million+r.interest_usd_million+r.amortization_usd_million signed_bridge_usd_million,
r.pretax_income_usd_million+r.corporate_usd_million+r.india_loss_usd_million+r.restructuring_usd_million+r.other_expense_usd_million+r.interest_usd_million+r.amortization_usd_million-SUM(p.operating_income_usd_million) pretax_bridge_residual_usd_million,
SUM(p.operating_income_usd_million)-r.reported_segment_operating_usd_million segment_sum_residual_usd_million FROM periods p JOIN recons r USING(fiscal_year,months) GROUP BY p.fiscal_year,p.months
SQL
cat > /logs/artifacts/service_subscriptions.sql <<'SQL'
WITH p AS (SELECT economic_date,MAX(CASE service WHEN 'Disney+' THEN subscriptions_million END) d,MAX(CASE service WHEN 'Hulu' THEN subscriptions_million END) h
FROM subscriptions WHERE economic_date IN ('2025-06-28','2025-09-27') GROUP BY economic_date)
SELECT c.economic_date,c.d disney_subscriptions_million,c.h hulu_subscriptions_million,c.d+c.h total_service_subscriptions_million,c.d+c.h-p.d-p.h sequential_change_million FROM p c JOIN p ON p.economic_date='2025-06-28'
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v13-a09",
  "tables": [
    {
      "id": "segment_model",
      "file": "segment_model.sql",
      "evidence": [
        "a09:s01"
      ]
    },
    {
      "id": "consolidated_bridge",
      "file": "consolidated_bridge.sql",
      "evidence": [
        "a09:s01"
      ]
    },
    {
      "id": "service_subscriptions",
      "file": "service_subscriptions.sql",
      "evidence": [
        "a09:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "unresolved",
      "evidence": [
        "a09:s02",
        "a09:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "a09:s02"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "a09:s02"
      ]
    }
  ]
}
ANSWER
