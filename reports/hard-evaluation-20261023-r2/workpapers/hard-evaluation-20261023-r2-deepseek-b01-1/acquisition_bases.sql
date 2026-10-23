WITH acq AS (
  SELECT
    deal,
    method,
    cash_shares + cash_awards AS listed_cash,
    cash_acquired,
    share_consideration + cvr_common + replacement_options + replacement_rsus + cvr_awards AS listed_noncash,
    unvested_award_charge,
    transaction_costs,
    reported_basis,
    required_disposal
  FROM acquisitions
),
bases AS (
  SELECT
    *,
    CASE
      WHEN method = 'business_combination' THEN listed_cash + listed_noncash
      WHEN method = 'asset_acquisition' THEN listed_cash - unvested_award_charge + transaction_costs
      ELSE listed_cash + listed_noncash
    END AS accounting_basis
  FROM acq
)
SELECT
  deal,
  accounting_basis AS accounting_basis_usd_million,
  accounting_basis - reported_basis AS reported_basis_residual_usd_million,
  listed_noncash AS noncash_consideration_usd_million,
  listed_cash - cash_acquired AS net_cash_paid_usd_million,
  listed_cash - unvested_award_charge - cash_acquired AS noncompensation_net_cash_usd_million,
  listed_cash - cash_acquired - required_disposal AS post_disposal_net_cash_usd_million
FROM bases;
