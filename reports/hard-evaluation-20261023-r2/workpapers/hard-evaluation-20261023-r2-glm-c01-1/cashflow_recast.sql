WITH cash AS (
    SELECT period, operating, investing, financing, net_cash_change
    FROM cash_flows
), policy AS (
    SELECT period, basis
    FROM facility_policy
), facility AS (
    SELECT period, dpp_collections, purchaser_payment
    FROM facility_flows
), recast AS (
    SELECT
        c.period,
        CASE
            WHEN p.basis = 'sale'
            THEN c.operating + COALESCE(f.dpp_collections, 0.0)
            ELSE c.operating
        END AS operating_cash,
        CASE
            WHEN p.basis = 'sale'
            THEN c.investing - COALESCE(f.dpp_collections, 0.0)
                 + COALESCE(f.purchaser_payment, 0.0)
            ELSE c.investing
        END AS investing_cash,
        CASE
            WHEN p.basis = 'sale'
            THEN c.financing - COALESCE(f.purchaser_payment, 0.0)
            ELSE c.financing
        END AS financing_cash,
        c.net_cash_change AS total_cash
    FROM cash AS c
    LEFT JOIN policy AS p ON p.period = c.period
    LEFT JOIN facility AS f ON f.period = c.period
)
SELECT
    period,
    operating_cash,
    investing_cash,
    financing_cash,
    total_cash
FROM recast
ORDER BY period;
