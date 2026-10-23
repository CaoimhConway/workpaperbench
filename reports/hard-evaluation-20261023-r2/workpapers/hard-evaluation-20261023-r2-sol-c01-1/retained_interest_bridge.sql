-- USD million. Opening/closing balances cover the prior sale facility.
-- A reduction in purchaser funding increases retained interest.
-- Credit-loss discounts reduce the retained interest; preserve the
-- net unexplained residual rather than attributing it to a cause.
-- The December 2024 reassignment is outside this cash-flow window.
WITH balance_changes AS (
    SELECT closing.purchaser_funding - opening.purchaser_funding
               AS funding_change,
           closing.dpp - opening.dpp AS reported_dpp_change
    FROM facility_balances AS opening
    JOIN facility_balances AS closing
      ON closing.sequence = opening.sequence + 1
), bridge AS (
    SELECT f.period,
           f.receivables_sold - f.new_transfer_cash AS new_dpp_from_transfers,
           b.funding_change,
           b.reported_dpp_change,
           f.receivables_sold - f.new_transfer_cash
               - f.dpp_collections - b.funding_change - l.loss_on_sale
               AS explained_dpp_change
    FROM facility_flows AS f
    JOIN facility_policy AS p ON p.period = f.period AND p.basis = 'sale'
    JOIN credit_losses AS l ON l.period = f.period
    CROSS JOIN balance_changes AS b
)
SELECT period, new_dpp_from_transfers, funding_change, reported_dpp_change,
       explained_dpp_change,
       reported_dpp_change - explained_dpp_change AS unallocated_dpp_change
FROM bridge;
