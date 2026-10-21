#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/booking_ratios.sql <<'SQL'
SELECT CAST(year AS INTEGER) year,CAST(quarter AS INTEGER) quarter,1000.0*gbv_usd_billion gbv_usd_million,nights_and_seats_million,
1000.0*gbv_usd_billion/nights_and_seats_million rounded_input_adr_usd,
1000.0*gbv_usd_billion/nights_and_seats_million-reported_adr_usd adr_rounding_residual_usd,
revenue_usd_million/(10.0*gbv_usd_billion) implied_revenue_to_gbv_pct FROM quarters WHERE year IN (2024,2025)
SQL
cat > /logs/artifacts/quarter_cash.sql <<'SQL'
SELECT CAST(year AS INTEGER) year,CAST(quarter AS INTEGER) quarter,operating_cash_usd_million-capex_usd_million fcf_usd_million,
100.0*(operating_cash_usd_million-capex_usd_million)/revenue_usd_million fcf_margin_pct,
100.0*adjusted_ebitda_usd_million/revenue_usd_million adjusted_ebitda_margin_pct FROM quarters WHERE year IN (2024,2025)
SQL
cat > /logs/artifacts/rolling_cash.sql <<'SQL'
WITH w AS (SELECT r.year,r.quarter,SUM(q.revenue_usd_million) revenue,SUM(q.operating_cash_usd_million-q.capex_usd_million) fcf,
r.reported_ttm_revenue_usd_million reported_revenue,r.reported_ttm_fcf_usd_million reported_fcf FROM rolling_disclosures r JOIN quarters q
ON q.year*4+q.quarter BETWEEN r.year*4+r.quarter-3 AND r.year*4+r.quarter WHERE r.year=2025 GROUP BY r.year,r.quarter)
SELECT CAST(year AS INTEGER) year,CAST(quarter AS INTEGER) quarter,revenue ttm_revenue_usd_million,fcf ttm_fcf_usd_million,
100.0*fcf/revenue ttm_fcf_margin_pct,revenue-reported_revenue revenue_residual_usd_million,fcf-reported_fcf fcf_residual_usd_million FROM w
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v11-b07",
  "tables": [
    {
      "id": "booking_ratios",
      "file": "booking_ratios.sql",
      "evidence": [
        "b07:s01",
        "b07:s02"
      ]
    },
    {
      "id": "quarter_cash",
      "file": "quarter_cash.sql",
      "evidence": [
        "b07:s02",
        "b07:s03"
      ]
    },
    {
      "id": "rolling_cash",
      "file": "rolling_cash.sql",
      "evidence": [
        "b07:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "unresolved",
      "evidence": [
        "b07:s01",
        "b07:s02"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "b07:s03"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "b07:s03"
      ]
    }
  ]
}
ANSWER
