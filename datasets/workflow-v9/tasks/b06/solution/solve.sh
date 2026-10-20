#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/segment_metrics.sql <<'SQL'
SELECT CAST(year AS INTEGER) year,segment,bookings_usd_million,revenue_usd_million,adjusted_ebitda_usd_million,
100.0*revenue_usd_million/bookings_usd_million revenue_to_bookings_pct,
100.0*adjusted_ebitda_usd_million/bookings_usd_million ebitda_to_bookings_pct FROM segments WHERE year IN (2024,2025)
SQL
cat > /logs/artifacts/corporate_bridge.sql <<'SQL'
WITH s AS (SELECT year,SUM(bookings_usd_million) b,SUM(revenue_usd_million) r,SUM(adjusted_ebitda_usd_million) e FROM segments GROUP BY year)
SELECT CAST(p.year AS INTEGER) year,e segment_sum_usd_million,p.corporate_cost_usd_million,e+p.corporate_cost_usd_million total_adjusted_ebitda_usd_million,
e+p.corporate_cost_usd_million-p.adjusted_ebitda_usd_million ebitda_residual_usd_million,
b-p.bookings_usd_million bookings_residual_usd_million,r-p.revenue_usd_million revenue_residual_usd_million,
100.0*(e+p.corporate_cost_usd_million)/b total_ebitda_to_bookings_pct FROM platform p JOIN s ON p.year=s.year WHERE p.year IN (2024,2025)
SQL
cat > /logs/artifacts/consumer_activity.sql <<'SQL'
SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,trips_million,mapcs_million,
1.0*trips_million/mapcs_million quarterly_trips_per_monthly_consumer,
1.0*trips_million/mapcs_million/months monthly_trips_per_monthly_consumer FROM platform WHERE year IN (2024,2025)
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v9-b06",
  "tables": [
    {
      "id": "segment_metrics",
      "file": "segment_metrics.sql",
      "evidence": [
        "b06:s01"
      ]
    },
    {
      "id": "corporate_bridge",
      "file": "corporate_bridge.sql",
      "evidence": [
        "b06:s01"
      ]
    },
    {
      "id": "consumer_activity",
      "file": "consumer_activity.sql",
      "evidence": [
        "b06:s02",
        "b06:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "b06:s01",
        "b06:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "b06:s01"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "b06:s02",
        "b06:s03"
      ]
    }
  ]
}
ANSWER
