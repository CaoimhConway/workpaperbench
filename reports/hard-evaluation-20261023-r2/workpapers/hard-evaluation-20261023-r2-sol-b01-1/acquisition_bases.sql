WITH components AS (
    SELECT deal, method, reported_basis, transaction_costs,
           unvested_award_charge, required_disposal,
           cash_shares + cash_awards AS listed_cash,
           share_consideration + cvr_common + replacement_options
               + replacement_rsus + cvr_awards AS noncash,
           cash_acquired
    FROM acquisitions
), reconstructed AS (
    SELECT *,
           listed_cash + noncash - unvested_award_charge
               + CASE WHEN method = 'asset_acquisition'
                      THEN transaction_costs ELSE 0.0 END AS accounting_basis,
           listed_cash - cash_acquired AS net_cash
    FROM components
)
SELECT deal,
       accounting_basis AS accounting_basis_usd_million,
       accounting_basis - reported_basis AS reported_basis_residual_usd_million,
       noncash AS noncash_consideration_usd_million,
       net_cash AS net_cash_paid_usd_million,
       net_cash - unvested_award_charge AS noncompensation_net_cash_usd_million,
       net_cash - required_disposal AS post_disposal_net_cash_usd_million
FROM reconstructed;
