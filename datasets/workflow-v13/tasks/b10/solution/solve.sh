#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/parent_earnings_bridge.sql <<'SQL'
WITH p AS (SELECT year,SUM(aftertax_parent_usd_million) total,
SUM(CASE WHEN measure='investment_gain' THEN aftertax_parent_usd_million ELSE 0 END) gain,
SUM(CASE WHEN measure='impairment' THEN aftertax_parent_usd_million ELSE 0 END) impairment FROM earnings_components GROUP BY year)
SELECT p.year,p.total parent_income_usd_million,p.gain investment_gain_usd_million,p.impairment signed_impairment_usd_million,
p.total-p.gain-p.impairment operating_earnings_usd_million,p.total-b.reported_parent_income_usd_million residual_usd_million
FROM p JOIN annual_bases b USING(year) WHERE p.year IN (2023,2024,2025)
SQL
cat > /logs/artifacts/consolidated_cash_bridge.sql <<'SQL'
SELECT b.year,b.reported_parent_income_usd_million parent_income_usd_million,b.consolidated_income_usd_million,
b.consolidated_income_usd_million-b.reported_parent_income_usd_million noncontrolling_income_usd_million,
SUM(a.signed_cash_adjustment_usd_million) signed_adjustment_usd_million,
b.consolidated_income_usd_million+SUM(a.signed_cash_adjustment_usd_million) operating_cash_usd_million,
b.consolidated_income_usd_million+SUM(a.signed_cash_adjustment_usd_million)-b.reported_operating_cash_usd_million residual_usd_million
FROM annual_bases b JOIN cash_adjustments a USING(year) WHERE b.year IN (2023,2024,2025) GROUP BY b.year
SQL
cat > /logs/artifacts/investment_gain_bridge.sql <<'SQL'
WITH p AS (SELECT year,SUM(CASE WHEN measure='equity_unrealized' THEN pretax_gain_usd_million ELSE 0 END) unrealized,
SUM(CASE WHEN measure='equity_sold' THEN pretax_gain_usd_million ELSE 0 END) sold,
SUM(CASE WHEN measure IN ('fixed_realized_gain','fixed_realized_loss') THEN pretax_gain_usd_million ELSE 0 END) fixed,
SUM(CASE WHEN measure='other' THEN pretax_gain_usd_million ELSE 0 END) other,SUM(pretax_gain_usd_million) total FROM investment_components GROUP BY year)
SELECT p.year,p.unrealized unrealized_equity_gain_usd_million,p.sold equity_sold_gain_usd_million,p.fixed fixed_net_gain_usd_million,p.other other_gain_usd_million,
p.total pretax_gain_usd_million,p.total+c.signed_cash_adjustment_usd_million cash_removal_residual_usd_million,
100.0*p.unrealized/p.total unrealized_to_net_gain_pct FROM p JOIN cash_adjustments c ON p.year=c.year AND c.measure='investment_gain' WHERE p.year IN (2023,2024,2025)
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v13-b10",
  "tables": [
    {
      "id": "parent_earnings_bridge",
      "file": "parent_earnings_bridge.sql",
      "evidence": [
        "b10:s01"
      ]
    },
    {
      "id": "consolidated_cash_bridge",
      "file": "consolidated_cash_bridge.sql",
      "evidence": [
        "b10:s01",
        "b10:s02"
      ]
    },
    {
      "id": "investment_gain_bridge",
      "file": "investment_gain_bridge.sql",
      "evidence": [
        "b10:s02",
        "b10:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "unresolved",
      "evidence": [
        "b10:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "b10:s03"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "b10:s01",
        "b10:s02"
      ]
    }
  ]
}
ANSWER
