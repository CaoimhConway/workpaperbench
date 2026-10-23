#!/bin/bash
set -euo pipefail
mkdir -p /logs/artifacts
cat > /logs/artifacts/cash_investment.sql <<'SQL'
WITH b AS (SELECT c.cash_ppe,a.*,1000.0*(p.capital_payables_billion-o.capital_payables_billion) payable_change,
 p.net-o.net net_change FROM cash_flows c JOIN annual_expenses a USING(year)
 JOIN ppe p ON p.year=c.year JOIN ppe o ON o.year=c.year-1) SELECT cash_ppe cash_ppe_usd_million,finance_principal_cash principal_usd_million,
 cash_ppe+finance_principal_cash capital_cash_usd_million,finance_rou_additions noncash_lease_additions_usd_million FROM b
SQL
cat > /logs/artifacts/ppe_bridge.sql <<'SQL'
WITH b AS (SELECT c.cash_ppe,a.*,1000.0*(p.capital_payables_billion-o.capital_payables_billion) payable_change,
 p.net-o.net net_change FROM cash_flows c JOIN annual_expenses a USING(year)
 JOIN ppe p ON p.year=c.year JOIN ppe o ON o.year=c.year-1) SELECT payable_change payables_change_usd_million,cash_ppe+payable_change purchase_proxy_usd_million,
 finance_rou_additions lease_additions_usd_million,1000.0*ppe_depreciation_billion depreciation_usd_million,
 net_change net_change_usd_million,cash_ppe+payable_change+finance_rou_additions-1000.0*ppe_depreciation_billion explained_change_usd_million,
 net_change-(cash_ppe+payable_change+finance_rou_additions-1000.0*ppe_depreciation_billion) residual_usd_million FROM b
SQL
cat > /logs/artifacts/lease_movements.sql <<'SQL'
WITH l AS (SELECT c.gross-p.gross gross,c.accumulated-p.accumulated accumulated,c.net-p.net net,
 a.finance_rou_additions additions,a.finance_amortization amort FROM finance_leases c JOIN finance_leases p ON p.year=c.year-1
 JOIN annual_expenses a ON a.year=c.year), bridge AS (
 SELECT 'gross' measure,gross observed,additions explained FROM l UNION ALL
 SELECT 'accumulated',accumulated,amort FROM l UNION ALL SELECT 'net',net,additions-amort FROM l)
 SELECT measure,observed change_usd_million,explained explained_change_usd_million,observed-explained residual_usd_million FROM bridge
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-hard-pilot-v1-b01",
  "tables": [
    {
      "id": "cash_investment",
      "file": "cash_investment.sql",
      "evidence": [
        "b01:s01",
        "b01:s03"
      ]
    },
    {
      "id": "ppe_bridge",
      "file": "ppe_bridge.sql",
      "evidence": [
        "b01:s01",
        "b01:s02",
        "b01:s03"
      ]
    },
    {
      "id": "lease_movements",
      "file": "lease_movements.sql",
      "evidence": [
        "b01:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "b01:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "b01:s03"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "unresolved",
      "evidence": [
        "b01:s01",
        "b01:s02",
        "b01:s03"
      ]
    }
  ]
}
ANSWER
