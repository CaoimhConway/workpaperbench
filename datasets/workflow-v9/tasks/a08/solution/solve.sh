#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/income_model.sql <<'SQL'
WITH p AS (SELECT i.*,a.amortization_usd_million,a.ordinary_sbc_usd_million,a.restructuring_acquisition_usd_million,
a.sbc_inside_restructuring_usd_million,a.reported_adjusted_operating_usd_million FROM income i JOIN adjustments a USING(fiscal_year,months) WHERE fiscal_year IN (2025,2026)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.subscription_usd_million-q.subscription_usd_million,
a.professional_usd_million-q.professional_usd_million,a.subscription_cost_usd_million-q.subscription_cost_usd_million,
a.professional_cost_usd_million-q.professional_cost_usd_million,a.operating_expense_usd_million-q.operating_expense_usd_million,
a.reported_operating_usd_million-q.reported_operating_usd_million,a.strategic_gain_usd_million-q.strategic_gain_usd_million,
a.other_income_usd_million-q.other_income_usd_million,a.signed_tax_usd_million-q.signed_tax_usd_million,a.reported_net_income_usd_million-q.reported_net_income_usd_million,
a.amortization_usd_million-q.amortization_usd_million,a.ordinary_sbc_usd_million-q.ordinary_sbc_usd_million,
a.restructuring_acquisition_usd_million-q.restructuring_acquisition_usd_million,a.sbc_inside_restructuring_usd_million-q.sbc_inside_restructuring_usd_million,
a.reported_adjusted_operating_usd_million-q.reported_adjusted_operating_usd_million FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.months=12 AND q.months=3),
base AS (SELECT *,subscription_usd_million+professional_usd_million rev,
subscription_usd_million+professional_usd_million-subscription_cost_usd_million-professional_cost_usd_million gp FROM periods),
computed AS (SELECT *,gp-operating_expense_usd_million op FROM base) SELECT fiscal_year,months,rev revenue_usd_million,gp gross_profit_usd_million,op operating_income_usd_million,
op+strategic_gain_usd_million+other_income_usd_million pretax_usd_million,
op+strategic_gain_usd_million+other_income_usd_million+signed_tax_usd_million net_income_usd_million,
op+strategic_gain_usd_million+other_income_usd_million+signed_tax_usd_million-reported_net_income_usd_million residual_usd_million FROM computed
SQL
cat > /logs/artifacts/operating_adjustment_bridge.sql <<'SQL'
WITH p AS (SELECT i.*,a.amortization_usd_million,a.ordinary_sbc_usd_million,a.restructuring_acquisition_usd_million,
a.sbc_inside_restructuring_usd_million,a.reported_adjusted_operating_usd_million FROM income i JOIN adjustments a USING(fiscal_year,months) WHERE fiscal_year IN (2025,2026)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.subscription_usd_million-q.subscription_usd_million,
a.professional_usd_million-q.professional_usd_million,a.subscription_cost_usd_million-q.subscription_cost_usd_million,
a.professional_cost_usd_million-q.professional_cost_usd_million,a.operating_expense_usd_million-q.operating_expense_usd_million,
a.reported_operating_usd_million-q.reported_operating_usd_million,a.strategic_gain_usd_million-q.strategic_gain_usd_million,
a.other_income_usd_million-q.other_income_usd_million,a.signed_tax_usd_million-q.signed_tax_usd_million,a.reported_net_income_usd_million-q.reported_net_income_usd_million,
a.amortization_usd_million-q.amortization_usd_million,a.ordinary_sbc_usd_million-q.ordinary_sbc_usd_million,
a.restructuring_acquisition_usd_million-q.restructuring_acquisition_usd_million,a.sbc_inside_restructuring_usd_million-q.sbc_inside_restructuring_usd_million,
a.reported_adjusted_operating_usd_million-q.reported_adjusted_operating_usd_million FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.months=12 AND q.months=3),
base AS (SELECT *,subscription_usd_million+professional_usd_million rev,
subscription_usd_million+professional_usd_million-subscription_cost_usd_million-professional_cost_usd_million gp FROM periods),
computed AS (SELECT *,gp-operating_expense_usd_million op FROM base) SELECT fiscal_year,months,amortization_usd_million+ordinary_sbc_usd_million+restructuring_acquisition_usd_million exclusion_usd_million,
sbc_inside_restructuring_usd_million already_in_restructuring_sbc_usd_million,
op+amortization_usd_million+ordinary_sbc_usd_million+restructuring_acquisition_usd_million adjusted_operating_usd_million,
100.0*(op+amortization_usd_million+ordinary_sbc_usd_million+restructuring_acquisition_usd_million)/rev adjusted_margin_pct,
op+amortization_usd_million+ordinary_sbc_usd_million+restructuring_acquisition_usd_million-reported_adjusted_operating_usd_million residual_usd_million FROM computed
SQL
cat > /logs/artifacts/acquisition_scope.sql <<'SQL'
SELECT c.months,c.subscription_usd_million+c.professional_usd_million current_revenue_usd_million,
p.subscription_usd_million+p.professional_usd_million prior_revenue_usd_million,a.total_revenue_usd_million acquired_revenue_usd_million,
c.subscription_usd_million+c.professional_usd_million-a.total_revenue_usd_million current_ex_disclosed_acquisition_usd_million,
100.0*((c.subscription_usd_million+c.professional_usd_million)/(p.subscription_usd_million+p.professional_usd_million)-1) reported_growth_pct,
100.0*((c.subscription_usd_million+c.professional_usd_million-a.total_revenue_usd_million)/(p.subscription_usd_million+p.professional_usd_million)-1) arithmetic_ex_acquisition_growth_pct,
c.subscription_usd_million-a.subscription_usd_million subscription_ex_acquisition_usd_million FROM income c JOIN income p ON c.months=p.months AND c.fiscal_year=2026 AND p.fiscal_year=2025
JOIN acquired_revenue a ON a.fiscal_year=c.fiscal_year AND a.months=c.months WHERE c.months IN (3,12)
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v9-a08",
  "tables": [
    {
      "id": "income_model",
      "file": "income_model.sql",
      "evidence": [
        "a08:s01"
      ]
    },
    {
      "id": "operating_adjustment_bridge",
      "file": "operating_adjustment_bridge.sql",
      "evidence": [
        "a08:s01",
        "a08:s02"
      ]
    },
    {
      "id": "acquisition_scope",
      "file": "acquisition_scope.sql",
      "evidence": [
        "a08:s01",
        "a08:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "supported",
      "evidence": [
        "a08:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "a08:s03"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "a08:s01",
        "a08:s03"
      ]
    }
  ]
}
ANSWER
