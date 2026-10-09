#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/cash_generation.sql <<'SQL'
WITH p AS (SELECT fiscal_year,months,
MAX(CASE WHEN measure='Net cash provided by (used in) operating activities' THEN amount_usd_million END) ocf,
-MAX(CASE WHEN measure='Purchases of property and equipment' THEN amount_usd_million END) purchase,
MAX(CASE WHEN measure='Proceeds from property and equipment sales and incentives' THEN amount_usd_million END) proceeds,
-MAX(CASE WHEN measure='Principal repayments of finance leases' THEN amount_usd_million END) lease,
-MAX(CASE WHEN measure='Principal repayments of financing obligations' THEN amount_usd_million END) obligation,
MAX(CASE WHEN measure='Net cash provided by (used in) investing activities' THEN amount_usd_million END) investing,
MAX(CASE WHEN measure='Net cash provided by (used in) financing activities' THEN amount_usd_million END) financing,
MAX(CASE WHEN measure='Foreign currency effect on cash, cash equivalents, and restricted cash' THEN amount_usd_million END) fx,
MAX(CASE WHEN measure='Net increase (decrease) in cash, cash equivalents, and restricted cash' THEN amount_usd_million END) net,
MAX(CASE WHEN measure='Assets acquired under operating leases' THEN amount_usd_million END) operating_assets,
MAX(CASE WHEN measure='Property and equipment acquired under finance leases, net of remeasurements and modifications' THEN amount_usd_million END) finance_assets,
MAX(CASE WHEN measure='Increase (decrease) in property and equipment acquired but not yet paid' THEN amount_usd_million END) unpaid
FROM cashflows WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.ocf-q.ocf,a.purchase-q.purchase,a.proceeds-q.proceeds,a.lease-q.lease,a.obligation-q.obligation,
a.investing-q.investing,a.financing-q.financing,a.fx-q.fx,a.net-q.net,a.operating_assets-q.operating_assets,a.finance_assets-q.finance_assets,a.unpaid-q.unpaid
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.months=12 AND q.months=3) SELECT fiscal_year,months,ocf operating_cash_usd_million,purchase gross_property_spending_usd_million,
proceeds sales_and_incentives_usd_million,purchase-proceeds net_property_spending_usd_million,ocf-purchase+proceeds issuer_fcf_usd_million,
ocf-purchase+proceeds-lease after_finance_lease_principal_usd_million,ocf-purchase+proceeds-lease-obligation after_all_capital_principal_usd_million FROM periods
SQL
cat > /logs/artifacts/cash_movement.sql <<'SQL'
WITH p AS (SELECT fiscal_year,months,
MAX(CASE WHEN measure='Net cash provided by (used in) operating activities' THEN amount_usd_million END) ocf,
-MAX(CASE WHEN measure='Purchases of property and equipment' THEN amount_usd_million END) purchase,
MAX(CASE WHEN measure='Proceeds from property and equipment sales and incentives' THEN amount_usd_million END) proceeds,
-MAX(CASE WHEN measure='Principal repayments of finance leases' THEN amount_usd_million END) lease,
-MAX(CASE WHEN measure='Principal repayments of financing obligations' THEN amount_usd_million END) obligation,
MAX(CASE WHEN measure='Net cash provided by (used in) investing activities' THEN amount_usd_million END) investing,
MAX(CASE WHEN measure='Net cash provided by (used in) financing activities' THEN amount_usd_million END) financing,
MAX(CASE WHEN measure='Foreign currency effect on cash, cash equivalents, and restricted cash' THEN amount_usd_million END) fx,
MAX(CASE WHEN measure='Net increase (decrease) in cash, cash equivalents, and restricted cash' THEN amount_usd_million END) net,
MAX(CASE WHEN measure='Assets acquired under operating leases' THEN amount_usd_million END) operating_assets,
MAX(CASE WHEN measure='Property and equipment acquired under finance leases, net of remeasurements and modifications' THEN amount_usd_million END) finance_assets,
MAX(CASE WHEN measure='Increase (decrease) in property and equipment acquired but not yet paid' THEN amount_usd_million END) unpaid
FROM cashflows WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.ocf-q.ocf,a.purchase-q.purchase,a.proceeds-q.proceeds,a.lease-q.lease,a.obligation-q.obligation,
a.investing-q.investing,a.financing-q.financing,a.fx-q.fx,a.net-q.net,a.operating_assets-q.operating_assets,a.finance_assets-q.finance_assets,a.unpaid-q.unpaid
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.months=12 AND q.months=3) SELECT fiscal_year,months,investing investing_cash_usd_million,financing financing_cash_usd_million,
fx currency_effect_usd_million,net cash_change_usd_million,ocf+investing+financing+fx-net residual_usd_million FROM periods
SQL
cat > /logs/artifacts/noncash_capital.sql <<'SQL'
WITH p AS (SELECT fiscal_year,months,
MAX(CASE WHEN measure='Net cash provided by (used in) operating activities' THEN amount_usd_million END) ocf,
-MAX(CASE WHEN measure='Purchases of property and equipment' THEN amount_usd_million END) purchase,
MAX(CASE WHEN measure='Proceeds from property and equipment sales and incentives' THEN amount_usd_million END) proceeds,
-MAX(CASE WHEN measure='Principal repayments of finance leases' THEN amount_usd_million END) lease,
-MAX(CASE WHEN measure='Principal repayments of financing obligations' THEN amount_usd_million END) obligation,
MAX(CASE WHEN measure='Net cash provided by (used in) investing activities' THEN amount_usd_million END) investing,
MAX(CASE WHEN measure='Net cash provided by (used in) financing activities' THEN amount_usd_million END) financing,
MAX(CASE WHEN measure='Foreign currency effect on cash, cash equivalents, and restricted cash' THEN amount_usd_million END) fx,
MAX(CASE WHEN measure='Net increase (decrease) in cash, cash equivalents, and restricted cash' THEN amount_usd_million END) net,
MAX(CASE WHEN measure='Assets acquired under operating leases' THEN amount_usd_million END) operating_assets,
MAX(CASE WHEN measure='Property and equipment acquired under finance leases, net of remeasurements and modifications' THEN amount_usd_million END) finance_assets,
MAX(CASE WHEN measure='Increase (decrease) in property and equipment acquired but not yet paid' THEN amount_usd_million END) unpaid
FROM cashflows WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.ocf-q.ocf,a.purchase-q.purchase,a.proceeds-q.proceeds,a.lease-q.lease,a.obligation-q.obligation,
a.investing-q.investing,a.financing-q.financing,a.fx-q.fx,a.net-q.net,a.operating_assets-q.operating_assets,a.finance_assets-q.finance_assets,a.unpaid-q.unpaid
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.months=12 AND q.months=3) SELECT fiscal_year,months,operating_assets operating_lease_assets_usd_million,
finance_assets finance_lease_property_usd_million,unpaid unpaid_property_change_usd_million FROM periods
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v7-a04",
  "tables": [
    {
      "id": "cash_generation",
      "file": "cash_generation.sql",
      "evidence": [
        "a04:s01",
        "a04:s02"
      ]
    },
    {
      "id": "cash_movement",
      "file": "cash_movement.sql",
      "evidence": [
        "a04:s01",
        "a04:s03"
      ]
    },
    {
      "id": "noncash_capital",
      "file": "noncash_capital.sql",
      "evidence": [
        "a04:s01"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "a04:s01",
        "a04:s02"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "a04:s01",
        "a04:s02"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "contradicted",
      "evidence": [
        "a04:s01"
      ]
    }
  ]
}
ANSWER
