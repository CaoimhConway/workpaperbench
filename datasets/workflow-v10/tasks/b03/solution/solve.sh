#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/annual_revenue_bridge.sql <<'SQL'
WITH components AS (SELECT measure,
MAX(CASE WHEN period='FY2024' THEN amount_usd_million END) p,
MAX(CASE WHEN period='FY2025' THEN amount_usd_million END) c FROM revenues
WHERE period IN ('FY2024','FY2025') AND measure IN ('consumer','institutional','other_transaction','stablecoin','blockchain_rewards','interest_finance','other_subscription','corporate_interest') GROUP BY measure),
totals AS (SELECT MAX(CASE WHEN period='FY2025' THEN amount_usd_million END)-MAX(CASE WHEN period='FY2024' THEN amount_usd_million END) delta
FROM revenues WHERE measure='total_revenue' AND period IN ('FY2024','FY2025'))
SELECT measure,p prior_usd_million,c current_usd_million,c-p change_usd_million,100.0*(c-p)/delta contribution_to_total_growth_pct FROM components CROSS JOIN totals
SQL
cat > /logs/artifacts/spot_revenue_proxy.sql <<'SQL'
SELECT s.segment,r.amount_usd_million revenue_usd_million,s.volume_usd_billion spot_volume_usd_billion,
100.0*r.amount_usd_million/(1000*s.volume_usd_billion) apparent_revenue_to_spot_pct
FROM spot_volume s JOIN revenues r ON r.period=s.period AND r.measure=s.segment WHERE s.period='Q4FY2025'
SQL
cat > /logs/artifacts/usdc_booked_ratio.sql <<'SQL'
SELECT scope,average_usdc_usd_billion,revenue_usd_million,
100.0*revenue_usd_million/(1000*average_usdc_usd_billion) quarter_booked_ratio_pct,
400.0*revenue_usd_million/(1000*average_usdc_usd_billion) annualized_booked_ratio_pct FROM usdc_economics WHERE period='Q4FY2025'
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v10-b03",
  "tables": [
    {
      "id": "annual_revenue_bridge",
      "file": "annual_revenue_bridge.sql",
      "evidence": [
        "b03:s01"
      ]
    },
    {
      "id": "spot_revenue_proxy",
      "file": "spot_revenue_proxy.sql",
      "evidence": [
        "b03:s01",
        "b03:s02"
      ]
    },
    {
      "id": "usdc_booked_ratio",
      "file": "usdc_booked_ratio.sql",
      "evidence": [
        "b03:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "b03:s01"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "b03:s01"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "b03:s02"
      ]
    }
  ]
}
ANSWER
