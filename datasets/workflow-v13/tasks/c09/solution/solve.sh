#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/bank_basis_bridge.sql <<'SQL'
SELECT period,managed_revenue_usd_million,managed_revenue_usd_million-fte_adjustment_usd_million printed_input_reported_basis_estimate_usd_million,
fte_adjustment_usd_million,100.0*expense_usd_million/managed_revenue_usd_million overhead_pct,
100.0*(expense_usd_million-legal_expense_usd_million)/managed_revenue_usd_million adjusted_overhead_pct,
nii_usd_million+nir_usd_million-managed_revenue_usd_million managed_revenue_residual_usd_million FROM bank_bases WHERE period IN ('Q4FY2025','FY2025')
SQL
cat > /logs/artifacts/significant_item_bridge.sql <<'SQL'
SELECT period,apple_pretax_reserve_usd_million,apple_aftertax_effect_usd_million,
apple_pretax_reserve_usd_million-apple_aftertax_effect_usd_million apple_tax_shield_usd_million,net_income_exclusion_change_usd_million,
reported_net_income_usd_million+net_income_exclusion_change_usd_million printed_input_adjusted_net_income_usd_million,
reported_net_income_usd_million+net_income_exclusion_change_usd_million-reported_adjusted_net_income_usd_million rounding_residual_usd_million
FROM significant_items WHERE period IN ('Q4FY2025','FY2025')
SQL
cat > /logs/artifacts/annual_exclusion_components.sql <<'SQL'
WITH a AS (SELECT * FROM significant_items WHERE period='FY2025'),d AS (SELECT * FROM annual_significant_details WHERE period='FY2025')
SELECT 'apple_reserve' measure,apple_aftertax_effect_usd_million signed_aftertax_exclusion_usd_million,'printed_after_tax' origin FROM a
UNION ALL SELECT 'first_republic_gain',-(apple_aftertax_effect_usd_million-d.corporate_tax_benefit_usd_million-net_income_exclusion_change_usd_million),'derived_after_tax' FROM a CROSS JOIN d
UNION ALL SELECT 'corporate_tax_benefit',-corporate_tax_benefit_usd_million,'printed_after_tax' FROM d
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v13-c09",
  "tables": [
    {
      "id": "bank_basis_bridge",
      "file": "bank_basis_bridge.sql",
      "evidence": [
        "c09:s01",
        "c09:s03"
      ]
    },
    {
      "id": "significant_item_bridge",
      "file": "significant_item_bridge.sql",
      "evidence": [
        "c09:s02"
      ]
    },
    {
      "id": "annual_exclusion_components",
      "file": "annual_exclusion_components.sql",
      "evidence": [
        "c09:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "c09:s01"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "c09:s02"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "c09:s02"
      ]
    }
  ]
}
ANSWER
