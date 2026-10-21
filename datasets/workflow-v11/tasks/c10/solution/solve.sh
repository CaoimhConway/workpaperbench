#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/regional_currency.sql <<'SQL'
SELECT region,current_revenue_usd_thousand+currency_adjustment_usd_thousand+current_hedging_exclusion_usd_thousand cc_current_usd_thousand,
prior_revenue_usd_thousand+prior_hedging_exclusion_usd_thousand unhedged_prior_usd_thousand,
100.0*(current_revenue_usd_thousand/prior_revenue_usd_thousand-1) reported_growth_pct,
100.0*((current_revenue_usd_thousand+currency_adjustment_usd_thousand+current_hedging_exclusion_usd_thousand)/(prior_revenue_usd_thousand+prior_hedging_exclusion_usd_thousand)-1) cc_growth_pct,
currency_adjustment_usd_thousand, current_hedging_exclusion_usd_thousand-prior_hedging_exclusion_usd_thousand hedging_exclusion_change_usd_thousand FROM regional_q4
SQL
cat > /logs/artifacts/annual_currency_margin.sql <<'SQL'
SELECT CAST(year AS INTEGER) year,revenue_usd_thousand-expense_usd_thousand operating_income_usd_thousand,
revenue_usd_thousand-revenue_fx_usd_thousand-expense_usd_thousand+expense_fx_usd_thousand adjusted_operating_income_usd_thousand,
100.0*(revenue_usd_thousand-expense_usd_thousand)/revenue_usd_thousand reported_margin_pct,
100.0*(revenue_usd_thousand-revenue_fx_usd_thousand-expense_usd_thousand+expense_fx_usd_thousand)/(revenue_usd_thousand-revenue_fx_usd_thousand) adjusted_margin_pct,
10000.0*((revenue_usd_thousand-revenue_fx_usd_thousand-expense_usd_thousand+expense_fx_usd_thousand)/(revenue_usd_thousand-revenue_fx_usd_thousand)-(revenue_usd_thousand-expense_usd_thousand)/revenue_usd_thousand) margin_change_bp,
revenue_usd_thousand-revenue_fx_usd_thousand-expense_usd_thousand+expense_fx_usd_thousand-reported_adjusted_operating_usd_thousand residual_usd_thousand
FROM annual_margin WHERE year=2025
SQL
cat > /logs/artifacts/forecast_bounds.sql <<'SQL'
SELECT CAST(f.year AS INTEGER) year,f.bound,f.revenue_usd_million,
100.0*(1000.0*f.revenue_usd_million/a.revenue_usd_thousand-1) implied_reported_revenue_growth_pct,
f.revenue_usd_million*f.target_operating_margin_pct/100.0 implied_operating_income_usd_million,
100.0*(10.0*f.revenue_usd_million*f.target_operating_margin_pct/(a.revenue_usd_thousand-a.expense_usd_thousand)-1) implied_operating_growth_pct,
f.included_acquisition_expense_usd_million FROM forecasts f CROSS JOIN annual_margin a WHERE f.year=2026 AND a.year=2025
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v11-c10",
  "tables": [
    {
      "id": "regional_currency",
      "file": "regional_currency.sql",
      "evidence": [
        "c10:s01"
      ]
    },
    {
      "id": "annual_currency_margin",
      "file": "annual_currency_margin.sql",
      "evidence": [
        "c10:s02"
      ]
    },
    {
      "id": "forecast_bounds",
      "file": "forecast_bounds.sql",
      "evidence": [
        "c10:s02",
        "c10:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "c10:s01",
        "c10:s02"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "c10:s03"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "c10:s03"
      ]
    }
  ]
}
ANSWER
