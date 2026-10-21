#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/cash_model.sql <<'SQL'
WITH p AS (SELECT fiscal_year,months,
MAX(CASE WHEN measure='Net income' THEN amount END) ni,
MAX(CASE WHEN measure='Net cash provided by operating activities' THEN amount END) ocf,
-MAX(CASE WHEN measure='Purchases of property and equipment' THEN amount END) pp,
-MAX(CASE WHEN measure='Principal payments on finance leases' THEN amount END) lease
FROM cashflows WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.ni-q.ni,a.ocf-q.ocf,a.pp-q.pp,a.lease-q.lease
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year WHERE a.months=12 AND q.months=3)
SELECT fiscal_year,months,ni net_income_usd_million,ocf operating_cash_usd_million,
pp property_spending_usd_million,lease lease_principal_usd_million,ocf-pp-lease free_cash_flow_usd_million,
ocf-pp-lease-ni fcf_less_net_income_usd_million FROM periods
SQL
cat > /logs/artifacts/operating_cash_bridge.sql <<'SQL'
WITH p AS (SELECT fiscal_year,months,
SUM(CASE WHEN measure IN ('Depreciation and amortization','Share-based compensation','Deferred income taxes',
'Unrealized (gain) loss on equity investments','Impairment charges for facilities consolidation','Other') THEN amount ELSE 0 END) nc,
SUM(CASE WHEN measure IN ('Accounts receivable','Prepaid expenses and other current assets','Other assets','Accounts payable',
'Accrued expenses and other current liabilities','Other liabilities') THEN amount ELSE 0 END) wc,
MAX(CASE WHEN measure='Net income' THEN amount END) ni,
MAX(CASE WHEN measure='Net cash provided by operating activities' THEN amount END) ocf
FROM cashflows WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.nc-q.nc,a.wc-q.wc,a.ni-q.ni,a.ocf-q.ocf
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year WHERE a.months=12 AND q.months=3)
SELECT fiscal_year,months,nc noncash_adjustments_usd_million,wc working_capital_change_usd_million,
ni+nc+wc-ocf residual_usd_million FROM periods
SQL
cat > /logs/artifacts/segment_model.sql <<'SQL'
WITH p AS (SELECT fiscal_year,months,segment,
MAX(CASE WHEN measure='revenue' THEN amount END) r,
MAX(CASE WHEN measure='operating_income' THEN amount END) oi
FROM segments WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months,segment),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.segment,a.r-q.r,a.oi-q.oi
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.segment=q.segment WHERE a.months=12 AND q.months=3)
SELECT fiscal_year,months,segment,r revenue_usd_million,oi operating_income_usd_million,
100.0*oi/r operating_margin_pct FROM periods
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v10-a02",
  "tables": [
    {
      "id": "cash_model",
      "file": "cash_model.sql",
      "evidence": [
        "a02:s01",
        "a02:s03"
      ]
    },
    {
      "id": "operating_cash_bridge",
      "file": "operating_cash_bridge.sql",
      "evidence": [
        "a02:s01"
      ]
    },
    {
      "id": "segment_model",
      "file": "segment_model.sql",
      "evidence": [
        "a02:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "a02:s01",
        "a02:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "a02:s02"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "supported",
      "evidence": [
        "a02:s01",
        "a02:s03"
      ]
    }
  ]
}
ANSWER
