#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/gross_profit_bases.sql <<'SQL'
WITH p AS (SELECT fiscal_year,CASE months WHEN 3 THEN 'Q2' ELSE 'H1' END window,revenue_usd_million revenue,
gaap_gross_profit_usd_million gaap,acquisition_adjustment_usd_million+stock_adjustment_usd_million+other_adjustment_usd_million adjustment,
reported_adjusted_gross_profit_usd_million reported,operating_cash_usd_million ocf,property_and_intangible_spending_usd_million purchase,
property_intangible_principal_usd_million principal,reported_fcf_usd_million fcf FROM financials WHERE fiscal_year IN (2025,2026) AND months IN (3,6)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,'Q1',a.revenue-q.revenue,a.gaap-q.gaap,a.adjustment-q.adjustment,
a.reported-q.reported,a.ocf-q.ocf,a.purchase-q.purchase,a.principal-q.principal,a.fcf-q.fcf FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.window='H1' AND q.window='Q2') SELECT fiscal_year,window,revenue revenue_usd_million,gaap gaap_gross_profit_usd_million,adjustment gross_adjustment_usd_million,
gaap+adjustment adjusted_gross_profit_usd_million,100.0*gaap/revenue gaap_gross_margin_pct,100.0*(gaap+adjustment)/revenue adjusted_gross_margin_pct,
gaap+adjustment-reported residual_usd_million FROM periods
SQL
cat > /logs/artifacts/current_h20_bridge.sql <<'SQL'
WITH p AS (SELECT fiscal_year,CASE months WHEN 3 THEN 'Q2' ELSE 'H1' END window,revenue_usd_million revenue,
gaap_gross_profit_usd_million gaap,acquisition_adjustment_usd_million+stock_adjustment_usd_million+other_adjustment_usd_million adjustment,
reported_adjusted_gross_profit_usd_million reported,operating_cash_usd_million ocf,property_and_intangible_spending_usd_million purchase,
property_intangible_principal_usd_million principal,reported_fcf_usd_million fcf FROM financials WHERE fiscal_year IN (2025,2026) AND months IN (3,6)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,'Q1',a.revenue-q.revenue,a.gaap-q.gaap,a.adjustment-q.adjustment,
a.reported-q.reported,a.ocf-q.ocf,a.purchase-q.purchase,a.principal-q.principal,a.fcf-q.fcf FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.window='H1' AND q.window='Q2') SELECT p.window,h.signed_charge_usd_million,p.gaap+p.adjustment+h.signed_charge_usd_million excluded_gross_profit_usd_million,
100.0*(p.gaap+p.adjustment+h.signed_charge_usd_million)/p.revenue excluded_gross_margin_pct,
p.gaap+p.adjustment+h.signed_charge_usd_million-h.reported_excluded_gross_profit_usd_million residual_usd_million
FROM periods p JOIN h20_current h ON p.window=h.window WHERE p.fiscal_year=2026
SQL
cat > /logs/artifacts/cash_generation.sql <<'SQL'
WITH p AS (SELECT fiscal_year,CASE months WHEN 3 THEN 'Q2' ELSE 'H1' END window,revenue_usd_million revenue,
gaap_gross_profit_usd_million gaap,acquisition_adjustment_usd_million+stock_adjustment_usd_million+other_adjustment_usd_million adjustment,
reported_adjusted_gross_profit_usd_million reported,operating_cash_usd_million ocf,property_and_intangible_spending_usd_million purchase,
property_intangible_principal_usd_million principal,reported_fcf_usd_million fcf FROM financials WHERE fiscal_year IN (2025,2026) AND months IN (3,6)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,'Q1',a.revenue-q.revenue,a.gaap-q.gaap,a.adjustment-q.adjustment,
a.reported-q.reported,a.ocf-q.ocf,a.purchase-q.purchase,a.principal-q.principal,a.fcf-q.fcf FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.window='H1' AND q.window='Q2') SELECT fiscal_year,window,ocf operating_cash_usd_million,purchase property_intangible_spending_usd_million,
principal property_intangible_principal_usd_million,ocf-purchase-principal fcf_usd_million,ocf-purchase-principal-fcf residual_usd_million FROM periods
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v2-a07",
  "tables": [
    {
      "id": "gross_profit_bases",
      "file": "gross_profit_bases.sql",
      "evidence": [
        "a07:s01"
      ]
    },
    {
      "id": "current_h20_bridge",
      "file": "current_h20_bridge.sql",
      "evidence": [
        "a07:s01"
      ]
    },
    {
      "id": "cash_generation",
      "file": "cash_generation.sql",
      "evidence": [
        "a07:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "release_raises_excluded_margin",
      "verdict": "contradicted",
      "evidence": [
        "a07:s01"
      ]
    },
    {
      "id": "china_zero_means_global_zero",
      "verdict": "contradicted",
      "evidence": [
        "a07:s03"
      ]
    },
    {
      "id": "exact_future_china_shipments",
      "verdict": "unresolved",
      "evidence": [
        "a07:s03"
      ]
    }
  ]
}
ANSWER
