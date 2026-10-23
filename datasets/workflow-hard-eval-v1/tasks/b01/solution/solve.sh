#!/bin/bash
set -euo pipefail
mkdir -p /logs/artifacts
cat > /logs/artifacts/acquisition_bases.sql <<'SQL'
WITH amounts AS (
 SELECT *,cash_shares+cash_awards cash,
 share_consideration+cvr_common+replacement_options+replacement_rsus+cvr_awards noncash
 FROM acquisitions
), deals AS (
 SELECT *,cash-cash_acquired net_cash,
 CASE WHEN method='business_combination' THEN cash+noncash
 ELSE cash-unvested_award_charge+transaction_costs END basis FROM amounts
) SELECT deal,basis accounting_basis_usd_million,
 basis-reported_basis reported_basis_residual_usd_million,noncash noncash_consideration_usd_million,
 net_cash net_cash_paid_usd_million,
 net_cash-unvested_award_charge noncompensation_net_cash_usd_million,
 net_cash-required_disposal post_disposal_net_cash_usd_million FROM deals
SQL
cat > /logs/artifacts/cash_coverage.sql <<'SQL'
WITH amounts AS (
 SELECT *,cash_shares+cash_awards cash,
 share_consideration+cvr_common+replacement_options+replacement_rsus+cvr_awards noncash
 FROM acquisitions
), deals AS (
 SELECT *,cash-cash_acquired net_cash,
 CASE WHEN method='business_combination' THEN cash+noncash
 ELSE cash-unvested_award_charge+transaction_costs END basis FROM amounts
) SELECT p.year,p.operating_cash+d.unvested_award_charge operating_cash_before_deal_compensation_usd_million,
 d.net_cash-d.unvested_award_charge identified_noncompensation_cash_usd_million,
 p.acquisition_payments-(d.net_cash-d.unvested_award_charge) other_acquisition_cash_usd_million,
 p.divestiture_proceeds-d.required_disposal other_divestiture_cash_usd_million,
 p.operating_cash-p.capex-p.acquisition_payments+p.divestiture_proceeds cash_after_portfolio_investment_usd_million
 FROM periods p JOIN deals d USING(year)
SQL
cat > /logs/artifacts/performance_views.sql <<'SQL'
WITH current AS (SELECT * FROM periods WHERE year=2020),
 prior AS (SELECT * FROM periods WHERE year=2019),
 comparable AS (SELECT * FROM proforma_revenue WHERE year=2019),
 charges AS (SELECT iprd_charge+sales_admin_award_charge+research_award_charge amount
 FROM acquisition_effects WHERE deal='MyoKardia')
 SELECT 'reported_revenue_growth_percent' measure,(c.revenue/p.revenue-1)*100 value FROM current c CROSS JOIN prior p
 UNION ALL SELECT 'proforma_baseline_revenue_growth_percent',(c.revenue/p.revenue-1)*100 FROM current c CROSS JOIN comparable p
 UNION ALL SELECT 'immediate_myokardia_expenses_usd_million',amount FROM charges
 UNION ALL SELECT 'selected_effects_excluded_pretax_usd_million',pretax+amount+contingent_fv_expense
 FROM current CROSS JOIN charges
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-hard-eval-v1-b01",
  "tables": [
    {
      "id": "acquisition_bases",
      "file": "acquisition_bases.sql",
      "evidence": [
        "b01:s01",
        "b01:s02",
        "b01:s07",
        "b01:s08"
      ]
    },
    {
      "id": "cash_coverage",
      "file": "cash_coverage.sql",
      "evidence": [
        "b01:s01",
        "b01:s02",
        "b01:s03",
        "b01:s04",
        "b01:s07",
        "b01:s08"
      ]
    },
    {
      "id": "performance_views",
      "file": "performance_views.sql",
      "evidence": [
        "b01:s02",
        "b01:s05",
        "b01:s06",
        "b01:s08"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "b01:s02"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "b01:s07"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "unresolved",
      "evidence": [
        "b01:s06",
        "b01:s08"
      ]
    }
  ]
}
ANSWER
