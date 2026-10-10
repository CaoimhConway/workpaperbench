#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/financial_versions.sql <<'SQL'
WITH p AS (SELECT *,product_revenue_usd_million+service_revenue_usd_million-product_cost_usd_million-service_cost_usd_million gp FROM income_versions
WHERE year IN (2024,2025) AND version IN ('release','annual'))
SELECT version,CAST(year AS INTEGER) year,gp gross_profit_usd_million,gp-operating_expense_usd_million operating_income_usd_million,
gp-operating_expense_usd_million+other_income_usd_million pretax_usd_million,
gp-operating_expense_usd_million+other_income_usd_million-tax_usd_million net_income_usd_million,
gp-operating_expense_usd_million+other_income_usd_million-tax_usd_million-net_income_usd_million residual_usd_million FROM p
SQL
cat > /logs/artifacts/settlement_revision_bridge.sql <<'SQL'
WITH p AS (SELECT version,product_cost_usd_million pc,
product_revenue_usd_million+service_revenue_usd_million-product_cost_usd_million-service_cost_usd_million gp,operating_expense_usd_million e,other_income_usd_million o,tax_usd_million t,net_income_usd_million n FROM income_versions WHERE year=2025),
v AS (SELECT version,'product_cost_usd_million' measure,pc value FROM p UNION ALL SELECT version,'gross_profit_usd_million',gp FROM p
UNION ALL SELECT version,'operating_income_usd_million',gp-e FROM p UNION ALL SELECT version,'pretax_usd_million',gp-e+o FROM p
UNION ALL SELECT version,'tax_usd_million',t FROM p UNION ALL SELECT version,'net_income_usd_million',n FROM p),
b AS (SELECT a.measure,r.value prior_release_usd_million,a.value annual_report_usd_million,a.value-r.value observed_change_usd_million,
CASE WHEN a.measure='product_cost_usd_million' THEN s.product_cost_charge_usd_million WHEN a.measure='tax_usd_million' THEN -s.tax_benefit_usd_million
WHEN a.measure='net_income_usd_million' THEN -s.product_cost_charge_usd_million+s.tax_benefit_usd_million ELSE -s.product_cost_charge_usd_million END settlement_effect_usd_million
FROM v a JOIN v r ON a.measure=r.measure AND a.version='annual' AND r.version='release' CROSS JOIN settlement s WHERE s.fiscal_year_charged=2025)
SELECT *,observed_change_usd_million-settlement_effect_usd_million residual_usd_million FROM b
SQL
cat > /logs/artifacts/cash_revision_bridge.sql <<'SQL'
SELECT a.measure,r.amount_usd_million prior_release_usd_million,a.amount_usd_million annual_report_usd_million,
a.amount_usd_million-r.amount_usd_million change_usd_million FROM cash_versions a JOIN cash_versions r
ON a.measure=r.measure AND a.year=r.year AND a.version='annual' AND r.version='release' WHERE a.year=2025
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v7-c07",
  "tables": [
    {
      "id": "financial_versions",
      "file": "financial_versions.sql",
      "evidence": [
        "c07:s01",
        "c07:s02"
      ]
    },
    {
      "id": "settlement_revision_bridge",
      "file": "settlement_revision_bridge.sql",
      "evidence": [
        "c07:s01",
        "c07:s02"
      ]
    },
    {
      "id": "cash_revision_bridge",
      "file": "cash_revision_bridge.sql",
      "evidence": [
        "c07:s01",
        "c07:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "supported",
      "evidence": [
        "c07:s01",
        "c07:s02"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "c07:s03"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "c07:s02"
      ]
    }
  ]
}
ANSWER
