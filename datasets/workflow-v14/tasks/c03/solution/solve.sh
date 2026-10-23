#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/gross_to_net.sql <<'SQL'
WITH p AS (SELECT period,
SUM(CASE WHEN measure IN ('service','data_processing','international','other') THEN amount_usd_million ELSE 0 END) g,
MAX(CASE WHEN measure='client_incentives' THEN amount_usd_million END) i,
MAX(CASE WHEN measure='net_revenue' THEN amount_usd_million END) n FROM revenue_components WHERE period IN ('FY2025','Q4FY2025') GROUP BY period),
periods AS (SELECT * FROM p UNION ALL SELECT '9MFY2025',a.g-q.g,a.i-q.i,a.n-q.n FROM p a JOIN p q ON a.period='FY2025' AND q.period='Q4FY2025')
SELECT period,g gross_revenue_usd_million,i incentives_usd_million,g+i net_revenue_usd_million,-100.0*i/g incentive_share_of_gross_pct,g+i-n residual_usd_million FROM periods
SQL
cat > /logs/artifacts/net_income_reconciliation.sql <<'SQL'
WITH p AS (SELECT period,MAX(CASE WHEN measure='gaap' THEN amount_usd_million END) g,
MAX(CASE WHEN measure='adjusted' THEN amount_usd_million END) reported,
SUM(CASE WHEN measure NOT IN ('gaap','adjusted') THEN amount_usd_million ELSE 0 END) a,
SUM(CASE WHEN measure='litigation' THEN amount_usd_million ELSE 0 END) l
FROM net_income_reconciliation WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025') GROUP BY period)
SELECT period,g gaap_income_usd_million,a after_tax_adjustments_usd_million,g+a adjusted_income_usd_million,l litigation_adjustment_usd_million,g+a-reported residual_usd_million FROM p
SQL
cat > /logs/artifacts/income_growth_bridge.sql <<'SQL'
WITH p AS (SELECT period,MAX(CASE WHEN measure='gaap' THEN amount_usd_million END) g,
MAX(CASE WHEN measure='adjusted' THEN amount_usd_million END) a FROM net_income_reconciliation GROUP BY period)
SELECT CASE WHEN c.period='FY2025' THEN 'FY' ELSE 'Q4FY' END window,c.g-p.g gaap_change_usd_million,c.a-p.a adjusted_change_usd_million,
100.0*(c.g/p.g-1) gaap_growth_pct,100.0*(c.a/p.a-1) adjusted_growth_pct,(c.a-c.g)-(p.a-p.g) gap_change_usd_million
FROM p c JOIN p p ON (c.period='FY2025' AND p.period='FY2024') OR (c.period='Q4FY2025' AND p.period='Q4FY2024')
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v14-c03",
  "tables": [
    {
      "id": "gross_to_net",
      "file": "gross_to_net.sql",
      "evidence": [
        "c03:s01"
      ]
    },
    {
      "id": "net_income_reconciliation",
      "file": "net_income_reconciliation.sql",
      "evidence": [
        "c03:s02"
      ]
    },
    {
      "id": "income_growth_bridge",
      "file": "income_growth_bridge.sql",
      "evidence": [
        "c03:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "c03:s02"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "c03:s02"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "c03:s01"
      ]
    }
  ]
}
ANSWER
