#!/bin/bash
set -euo pipefail
mkdir -p /logs/artifacts
cat > /logs/artifacts/worldwide_mix.sql <<'SQL'
SELECT business_line,net_sales net_sales_usd_million,net_sales-cost_of_sales gross_profit_usd_million,
 100.0*(net_sales-cost_of_sales)/net_sales gross_margin_pct FROM business_lines
SQL
cat > /logs/artifacts/regional_product_bounds.sql <<'SQL'
WITH lines AS (SELECT MAX(CASE WHEN business_line='products' THEN net_sales END) p,
 MAX(CASE WHEN business_line='services' THEN net_sales END) s,
 MAX(CASE WHEN business_line='products' THEN (net_sales-cost_of_sales)/net_sales END) pm,
 MAX(CASE WHEN business_line='services' THEN (net_sales-cost_of_sales)/net_sales END) sm FROM business_lines),
 r AS (SELECT g.*,s.products_loss_pct/100.0 pr,s.services_loss_pct/100.0 sr,
 ROW_NUMBER() OVER(ORDER BY g.geography) rn FROM geographies g JOIN stress_rates s USING(geography)) SELECT geography,MAX(0,net_sales-s) lower_usd_million,
 MIN(net_sales,p) upper_usd_million FROM r CROSS JOIN lines
SQL
cat > /logs/artifacts/stress_bounds.sql <<'SQL'
WITH lines AS (SELECT MAX(CASE WHEN business_line='products' THEN net_sales END) p,
 MAX(CASE WHEN business_line='services' THEN net_sales END) s,
 MAX(CASE WHEN business_line='products' THEN (net_sales-cost_of_sales)/net_sales END) pm,
 MAX(CASE WHEN business_line='services' THEN (net_sales-cost_of_sales)/net_sales END) sm FROM business_lines),
 r AS (SELECT g.*,s.products_loss_pct/100.0 pr,s.services_loss_pct/100.0 sr,
 ROW_NUMBER() OVER(ORDER BY g.geography) rn FROM geographies g JOIN stress_rates s USING(geography)) , limits AS (SELECT 0 bound UNION ALL SELECT 1),
 candidates AS (SELECT a.geography ga,b.geography gb,c.geography gc,
 a.net_sales*x.bound sa,b.net_sales*y.bound sb,s-a.net_sales*x.bound-b.net_sales*y.bound sc
 FROM r a JOIN r b ON a.rn<b.rn JOIN r c ON c.rn!=a.rn AND c.rn!=b.rn
 CROSS JOIN limits x CROSS JOIN limits y CROSS JOIN lines
 WHERE s-a.net_sales*x.bound-b.net_sales*y.bound BETWEEN 0 AND c.net_sales),
 objectives AS (SELECT 'revenue' measure,1.0 pw,1.0 sw,p+s base FROM lines UNION ALL
 SELECT 'gross_profit',pm,sm,p*pm+s*sm FROM lines),
 losses AS (SELECT o.measure,o.base,v.ga,v.gb,v.gc,v.sa,v.sb,v.sc,
 SUM((r.net_sales-CASE r.geography WHEN v.ga THEN v.sa WHEN v.gb THEN v.sb ELSE v.sc END)*r.pr*o.pw+
 (CASE r.geography WHEN v.ga THEN v.sa WHEN v.gb THEN v.sb ELSE v.sc END)*r.sr*o.sw) loss
 FROM candidates v CROSS JOIN r CROSS JOIN objectives o GROUP BY o.measure,o.base,v.ga,v.gb,v.gc,v.sa,v.sb,v.sc)
 SELECT measure,MIN(loss) lower_usd_million,MAX(loss) upper_usd_million,
 100.0*MIN(loss)/base lower_pct,100.0*MAX(loss)/base upper_pct FROM losses GROUP BY measure,base
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-hard-pilot-v1-c01",
  "tables": [
    {
      "id": "worldwide_mix",
      "file": "worldwide_mix.sql",
      "evidence": [
        "c01:s01"
      ]
    },
    {
      "id": "regional_product_bounds",
      "file": "regional_product_bounds.sql",
      "evidence": [
        "c01:s01",
        "c01:s02"
      ]
    },
    {
      "id": "stress_bounds",
      "file": "stress_bounds.sql",
      "evidence": [
        "c01:s01",
        "c01:s02",
        "c01:s04"
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
        "c01:s04"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "c01:s01"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "unresolved",
      "evidence": [
        "c01:s01",
        "c01:s02"
      ]
    }
  ]
}
ANSWER
