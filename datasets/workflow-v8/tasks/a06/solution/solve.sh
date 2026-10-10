#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/income_model.sql <<'SQL'
WITH p AS (SELECT i.*,a.phonepe_sbc_usd_million,a.legal_usd_million,a.reorganization_usd_million,a.reported_adjusted_usd_million,
a.adjusted_currency_usd_million,a.reported_adjusted_cc_usd_million FROM income i JOIN adjustments a USING(fiscal_year,months) WHERE fiscal_year IN (2025,2026)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,6,a.revenue_usd_million-q.revenue_usd_million,a.cost_sales_usd_million-q.cost_sales_usd_million,
a.sga_usd_million-q.sga_usd_million,a.operating_income_usd_million-q.operating_income_usd_million,
a.phonepe_sbc_usd_million-q.phonepe_sbc_usd_million,a.legal_usd_million-q.legal_usd_million,a.reorganization_usd_million-q.reorganization_usd_million,
a.reported_adjusted_usd_million-q.reported_adjusted_usd_million,a.adjusted_currency_usd_million-q.adjusted_currency_usd_million,a.reported_adjusted_cc_usd_million-q.reported_adjusted_cc_usd_million
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.months=9 AND q.months=3),
computed AS (SELECT *,revenue_usd_million-cost_sales_usd_million-sga_usd_million op,
revenue_usd_million-cost_sales_usd_million-sga_usd_million+phonepe_sbc_usd_million+legal_usd_million+reorganization_usd_million adjusted FROM periods) SELECT fiscal_year,months,revenue_usd_million,op gaap_operating_income_usd_million,
adjusted adjusted_operating_income_usd_million,adjusted+adjusted_currency_usd_million adjusted_cc_operating_income_usd_million,
100.0*op/revenue_usd_million gaap_margin_pct,100.0*adjusted/revenue_usd_million adjusted_margin_pct FROM computed
SQL
cat > /logs/artifacts/adjustment_bridge.sql <<'SQL'
WITH p AS (SELECT i.*,a.phonepe_sbc_usd_million,a.legal_usd_million,a.reorganization_usd_million,a.reported_adjusted_usd_million,
a.adjusted_currency_usd_million,a.reported_adjusted_cc_usd_million FROM income i JOIN adjustments a USING(fiscal_year,months) WHERE fiscal_year IN (2025,2026)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,6,a.revenue_usd_million-q.revenue_usd_million,a.cost_sales_usd_million-q.cost_sales_usd_million,
a.sga_usd_million-q.sga_usd_million,a.operating_income_usd_million-q.operating_income_usd_million,
a.phonepe_sbc_usd_million-q.phonepe_sbc_usd_million,a.legal_usd_million-q.legal_usd_million,a.reorganization_usd_million-q.reorganization_usd_million,
a.reported_adjusted_usd_million-q.reported_adjusted_usd_million,a.adjusted_currency_usd_million-q.adjusted_currency_usd_million,a.reported_adjusted_cc_usd_million-q.reported_adjusted_cc_usd_million
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.months=9 AND q.months=3),
computed AS (SELECT *,revenue_usd_million-cost_sales_usd_million-sga_usd_million op,
revenue_usd_million-cost_sales_usd_million-sga_usd_million+phonepe_sbc_usd_million+legal_usd_million+reorganization_usd_million adjusted FROM periods) SELECT fiscal_year,months,phonepe_sbc_usd_million,legal_usd_million,reorganization_usd_million,
adjusted_currency_usd_million,op-operating_income_usd_million gaap_residual_usd_million,
adjusted-reported_adjusted_usd_million adjusted_residual_usd_million,
adjusted+adjusted_currency_usd_million-reported_adjusted_cc_usd_million cc_residual_usd_million FROM computed
SQL
cat > /logs/artifacts/year_to_date_cash.sql <<'SQL'
SELECT fiscal_year,months,operating_cash_usd_million,capital_spending_usd_million,
operating_cash_usd_million-capital_spending_usd_million free_cash_flow_usd_million,
operating_cash_usd_million-capital_spending_usd_million-reported_fcf_usd_million residual_usd_million FROM cashflows WHERE fiscal_year IN (2025,2026) AND months=9
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v8-a06",
  "tables": [
    {
      "id": "income_model",
      "file": "income_model.sql",
      "evidence": [
        "a06:s01",
        "a06:s02"
      ]
    },
    {
      "id": "adjustment_bridge",
      "file": "adjustment_bridge.sql",
      "evidence": [
        "a06:s01",
        "a06:s02"
      ]
    },
    {
      "id": "year_to_date_cash",
      "file": "year_to_date_cash.sql",
      "evidence": [
        "a06:s03"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "supported",
      "evidence": [
        "a06:s01",
        "a06:s02"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "a06:s03"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "a06:s03"
      ]
    }
  ]
}
ANSWER
