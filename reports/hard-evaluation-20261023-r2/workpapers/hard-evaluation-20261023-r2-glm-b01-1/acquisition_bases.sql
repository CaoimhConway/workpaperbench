WITH deal_components AS (
    SELECT
        deal,
        method,
        cash_shares,
        cash_awards,
        share_consideration,
        cvr_common,
        replacement_options,
        replacement_rsus,
        cvr_awards,
        unvested_award_charge,
        transaction_costs,
        cash_acquired,
        reported_basis,
        required_disposal
    FROM acquisitions
),
derived_deal_values AS (
    SELECT
        deal,
        CASE
            WHEN method = 'business_combination' THEN
                cash_shares
                + cash_awards
                + share_consideration
                + cvr_common
                + replacement_options
                + replacement_rsus
                + cvr_awards
            WHEN method = 'asset_acquisition' THEN
                cash_shares
                + cash_awards
                - unvested_award_charge
                + transaction_costs
        END AS accounting_basis,
        reported_basis,
        share_consideration
        + cvr_common
        + replacement_options
        + replacement_rsus
        + cvr_awards AS noncash_consideration,
        cash_shares
        + cash_awards
        - cash_acquired AS net_cash_paid,
        CASE
            WHEN method = 'asset_acquisition' THEN unvested_award_charge
            ELSE 0.0
        END AS compensation_cash,
        required_disposal
    FROM deal_components
)
SELECT
    deal,
    accounting_basis AS accounting_basis_usd_million,
    accounting_basis - reported_basis AS reported_basis_residual_usd_million,
    noncash_consideration AS noncash_consideration_usd_million,
    net_cash_paid AS net_cash_paid_usd_million,
    net_cash_paid - compensation_cash AS noncompensation_net_cash_usd_million,
    net_cash_paid - required_disposal AS post_disposal_net_cash_usd_million
FROM derived_deal_values
ORDER BY deal;
