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
