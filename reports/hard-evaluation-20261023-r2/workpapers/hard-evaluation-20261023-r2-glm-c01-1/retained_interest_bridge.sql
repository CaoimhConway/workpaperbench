WITH opening AS (
    SELECT purchaser_funding, dpp
    FROM facility_balances
    WHERE as_of = '2023-12-31'
), closing AS (
    SELECT purchaser_funding, dpp
    FROM facility_balances
    WHERE as_of = '2024-09-30'
), flows AS (
    SELECT period, receivables_sold, new_transfer_cash, dpp_collections
    FROM facility_flows
    WHERE period = '2024-9m'
), bridge AS (
    SELECT
        f.period,
        f.receivables_sold - f.new_transfer_cash AS new_dpp_from_transfers,
        c.purchaser_funding - o.purchaser_funding AS funding_change,
        c.dpp - o.dpp AS reported_dpp_change,
        (f.receivables_sold - f.new_transfer_cash)
          - f.dpp_collections
          - (c.purchaser_funding - o.purchaser_funding) AS explained_dpp_change
    FROM flows AS f
    CROSS JOIN opening AS o
    CROSS JOIN closing AS c
)
SELECT
    period,
    new_dpp_from_transfers,
    funding_change,
    reported_dpp_change,
    explained_dpp_change,
    reported_dpp_change - explained_dpp_change AS unallocated_dpp_change
FROM bridge;
