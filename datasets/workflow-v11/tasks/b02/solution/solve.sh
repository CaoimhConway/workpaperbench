#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/qualified_coverage.sql <<'SQL'
WITH holdings AS (SELECT DISTINCT * FROM treasury_holdings),t AS (
SELECT economic_date,COUNT(*) n,SUM(par_usd) par,SUM(cost_usd) cost,SUM(fair_value_usd) fv
FROM holdings GROUP BY economic_date) SELECT o.economic_date,o.cash_usd+o.repo_fair_value_usd+t.fv assets_usd,
o.redeemable_tokens,100.0*(o.cash_usd+o.repo_fair_value_usd+t.fv)/o.redeemable_tokens coverage_pct,
o.cash_usd+o.repo_fair_value_usd+t.fv-o.redeemable_tokens surplus_usd,
o.cash_usd+o.repo_fair_value_usd+t.fv-o.reported_assets_usd residual_usd,
CAST(julianday(o.signature_date)-julianday(o.economic_date) AS INTEGER) days_to_signature
FROM reserve_observations o JOIN t USING(economic_date)
WHERE o.economic_date IN ('2026-01-30','2026-02-10','2026-02-27')
SQL
cat > /logs/artifacts/treasury_valuation.sql <<'SQL'
WITH holdings AS (SELECT DISTINCT * FROM treasury_holdings),t AS (
SELECT economic_date,COUNT(*) n,SUM(par_usd) par,SUM(cost_usd) cost,SUM(fair_value_usd) fv
FROM holdings GROUP BY economic_date) SELECT o.economic_date,t.n distinct_holdings,t.par par_usd,t.cost cost_usd,t.fv fair_value_usd,
t.fv-t.cost valuation_gain_usd,t.fv-t.par discount_to_par_usd,t.fv-o.treasury_fair_value_usd residual_usd
FROM reserve_observations o JOIN t USING(economic_date)
WHERE o.economic_date IN ('2026-01-30','2026-02-10','2026-02-27')
SQL
cat > /logs/artifacts/stock_bridge.sql <<'SQL'
SELECT p.economic_date prior_date,c.economic_date current_date,
c.cash_usd-p.cash_usd cash_change_usd,c.repo_fair_value_usd-p.repo_fair_value_usd repo_change_usd,
c.treasury_fair_value_usd-p.treasury_fair_value_usd treasury_change_usd,
c.reported_assets_usd-p.reported_assets_usd asset_change_usd,c.redeemable_tokens-p.redeemable_tokens token_change,
(c.reported_assets_usd-c.redeemable_tokens)-(p.reported_assets_usd-p.redeemable_tokens) surplus_change_usd
FROM reserve_observations p JOIN reserve_observations c ON
(p.economic_date='2026-01-30' AND c.economic_date='2026-02-10') OR
(p.economic_date='2026-02-10' AND c.economic_date='2026-02-27')
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v11-b02",
  "tables": [
    {
      "id": "qualified_coverage",
      "file": "qualified_coverage.sql",
      "evidence": [
        "b02:s01",
        "b02:s02",
        "b02:s05"
      ]
    },
    {
      "id": "treasury_valuation",
      "file": "treasury_valuation.sql",
      "evidence": [
        "b02:s01",
        "b02:s02",
        "b02:s05"
      ]
    },
    {
      "id": "stock_bridge",
      "file": "stock_bridge.sql",
      "evidence": [
        "b02:s01",
        "b02:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "b02:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "b02:s04"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "b02:s01",
        "b02:s02",
        "b02:s05"
      ]
    }
  ]
}
ANSWER
