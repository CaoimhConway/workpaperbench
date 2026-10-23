#!/bin/bash
set -euo pipefail
mkdir -p /logs/artifacts
cat > /logs/artifacts/cashflow_recast.sql <<'SQL'
WITH recast AS (
 SELECT c.*,c.operating+CASE WHEN p.basis='sale' THEN f.dpp_collections ELSE 0 END operating_cash,
 c.investing-CASE WHEN p.basis='sale' THEN f.dpp_collections-f.purchaser_payment ELSE 0 END investing_cash,
 c.financing-CASE WHEN p.basis='sale' THEN f.purchaser_payment ELSE 0 END financing_cash
 FROM cash_flows c JOIN facility_policy p USING(period)
 LEFT JOIN facility_flows f USING(period)
) SELECT period,operating_cash,investing_cash,financing_cash,
 operating_cash+investing_cash+financing_cash total_cash FROM recast
SQL
cat > /logs/artifacts/cash_generation_change.sql <<'SQL'
WITH recast AS (
 SELECT c.*,c.operating+CASE WHEN p.basis='sale' THEN f.dpp_collections ELSE 0 END operating_cash,
 c.investing-CASE WHEN p.basis='sale' THEN f.dpp_collections-f.purchaser_payment ELSE 0 END investing_cash,
 c.financing-CASE WHEN p.basis='sale' THEN f.purchaser_payment ELSE 0 END financing_cash
 FROM cash_flows c JOIN facility_policy p USING(period)
 LEFT JOIN facility_flows f USING(period)
) , changes AS (
 SELECT n.operating-o.operating reported_operating_change,
 n.operating_cash-o.operating_cash normalized_operating_change,
 n.collateral-o.collateral collateral_change,n.capex-o.capex capex_change
 FROM recast o JOIN recast n ON n.sequence=o.sequence+1
) SELECT reported_operating_change,normalized_operating_change,
 reported_operating_change-normalized_operating_change presentation_effect,
 collateral_change,normalized_operating_change-collateral_change other_operating_change,
 normalized_operating_change-capex_change normalized_after_capex_change,
 normalized_operating_change-collateral_change-capex_change other_after_capex_change
 FROM changes
SQL
cat > /logs/artifacts/retained_interest_bridge.sql <<'SQL'
WITH movements AS (
 SELECT f.period,f.receivables_sold-f.new_transfer_cash new_dpp_from_transfers,
 e.purchaser_funding-b.purchaser_funding funding_change,e.dpp-b.dpp reported_dpp_change,
 c.noncash_dpp-f.dpp_collections-(e.purchaser_funding-b.purchaser_funding) explained_dpp_change
 FROM cash_flows c JOIN facility_flows f USING(period)
 CROSS JOIN facility_balances b JOIN facility_balances e ON e.sequence=b.sequence+1
) SELECT *,reported_dpp_change-explained_dpp_change unallocated_dpp_change FROM movements
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-hard-eval-v1-c01",
  "tables": [
    {
      "id": "cashflow_recast",
      "file": "cashflow_recast.sql",
      "evidence": [
        "c01:s01",
        "c01:s02",
        "c01:s03",
        "c01:s07"
      ]
    },
    {
      "id": "cash_generation_change",
      "file": "cash_generation_change.sql",
      "evidence": [
        "c01:s01",
        "c01:s02",
        "c01:s03",
        "c01:s07"
      ]
    },
    {
      "id": "retained_interest_bridge",
      "file": "retained_interest_bridge.sql",
      "evidence": [
        "c01:s01",
        "c01:s02",
        "c01:s05",
        "c01:s07"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "c01:s01",
        "c01:s02",
        "c01:s03",
        "c01:s07"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "c01:s01",
        "c01:s02",
        "c01:s03",
        "c01:s07"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "unresolved",
      "evidence": [
        "c01:s04"
      ]
    }
  ]
}
ANSWER
