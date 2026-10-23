#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/category_margin.sql <<'SQL'
WITH p AS (SELECT year,months,'product' category,product_revenue_usd_million r,product_cost_usd_million c FROM income
UNION ALL SELECT year,months,'service',service_revenue_usd_million,service_cost_usd_million FROM income)
SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,category,r-c gross_profit_usd_million,100.0*(r-c)/r margin_pct FROM p WHERE year IN (2024,2025)
SQL
cat > /logs/artifacts/net_income_growth_bridge.sql <<'SQL'
WITH parts AS (SELECT year,months,'product_gp' measure,product_revenue_usd_million-product_cost_usd_million v FROM income
UNION ALL SELECT year,months,'service_gp',service_revenue_usd_million-service_cost_usd_million FROM income
UNION ALL SELECT year,months,'research',-research_usd_million FROM income
UNION ALL SELECT year,months,'selling',-selling_usd_million FROM income
UNION ALL SELECT year,months,'other',other_income_usd_million FROM income
UNION ALL SELECT year,months,'tax',-tax_usd_million FROM income)
SELECT CAST(c.months AS INTEGER) months,c.measure,p.v prior_signed_usd_million,c.v current_signed_usd_million,c.v-p.v change_usd_million,
100.0*(c.v-p.v)/(ci.net_income_usd_million-pi.net_income_usd_million) contribution_to_net_income_growth_pct
FROM parts c JOIN parts p ON c.measure=p.measure AND c.months=p.months AND c.year=2025 AND p.year=2024
JOIN income ci ON ci.year=c.year AND ci.months=c.months JOIN income pi ON pi.year=p.year AND pi.months=p.months
SQL
cat > /logs/artifacts/prior_tax_baseline.sql <<'SQL'
SELECT CAST(c.months AS INTEGER) months,p.net_income_usd_million prior_gaap_usd_million,a.tax_charge_usd_million,
p.net_income_usd_million+a.tax_charge_usd_million prior_adjusted_usd_million,c.net_income_usd_million current_gaap_usd_million,
100.0*(c.net_income_usd_million/p.net_income_usd_million-1) gaap_growth_pct,
100.0*(c.net_income_usd_million/(p.net_income_usd_million+a.tax_charge_usd_million)-1) current_gaap_growth_vs_adjusted_prior_pct,
p.net_income_usd_million+a.tax_charge_usd_million-a.reported_adjusted_net_income_usd_million residual_usd_million
FROM income c JOIN income p ON c.months=p.months AND c.year=2025 AND p.year=2024
JOIN prior_tax_adjustments a ON a.year=p.year AND a.months=p.months
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v15-c05",
  "tables": [
    {
      "id": "category_margin",
      "file": "category_margin.sql",
      "evidence": [
        "c05:s01"
      ]
    },
    {
      "id": "net_income_growth_bridge",
      "file": "net_income_growth_bridge.sql",
      "evidence": [
        "c05:s01"
      ]
    },
    {
      "id": "prior_tax_baseline",
      "file": "prior_tax_baseline.sql",
      "evidence": [
        "c05:s01",
        "c05:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "c05:s01"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "c05:s01",
        "c05:s03"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "c05:s01",
        "c05:s02"
      ]
    }
  ]
}
ANSWER
