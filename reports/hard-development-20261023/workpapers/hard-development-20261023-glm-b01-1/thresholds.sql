WITH
basis AS (
    SELECT basic_shares, award_shares
    FROM eps_basis
),
note_inputs AS (
    SELECT
        n.note,
        n.principal,
        n.coupon,
        n.amortization,
        c.principal_settlement,
        n.principal * c.conversion_rate / 1000.0 AS full_shares_million
    FROM notes AS n
    JOIN contract_terms AS c ON c.note = n.note
),
portfolio AS (
    SELECT
        t.price,
        t.target_shares,
        b.basic_shares,
        b.award_shares,
        (
            SELECT SUM(n.full_shares_million)
            FROM note_inputs AS n
            WHERE n.principal_settlement = 'choice'
        ) AS optional_full_shares,
        (
            SELECT SUM(n.full_shares_million)
            FROM note_inputs AS n
            WHERE n.principal_settlement = 'cash'
        ) AS cash_full_shares,
        (
            SELECT SUM(n.principal)
            FROM note_inputs AS n
            WHERE n.principal_settlement = 'cash'
        ) AS cash_principal
    FROM threshold_case AS t
    CROSS JOIN basis AS b
),
optional_notes AS (
    SELECT
        note,
        full_shares_million AS shares,
        coupon + amortization AS addback
    FROM note_inputs
    WHERE principal_settlement = 'choice'
      AND note IN ('2025', '2027')
),
ranked_optional AS (
    SELECT
        o.note,
        o.shares,
        o.addback,
        COALESCE(
            (
                SELECT SUM(prior.shares)
                FROM optional_notes AS prior
                WHERE prior.addback / prior.shares < o.addback / o.shares
            ),
            0.0
        ) AS prior_shares,
        COALESCE(
            (
                SELECT SUM(prior.addback)
                FROM optional_notes AS prior
                WHERE prior.addback / prior.shares < o.addback / o.shares
            ),
            0.0
        ) AS prior_addback
    FROM optional_notes AS o
),
results AS (
    SELECT
        p.price,
        p.target_shares,
        p.cash_principal
            / (p.optional_full_shares + p.cash_full_shares - p.target_shares)
            AS share_price,
        CASE
            WHEN p.cash_full_shares * p.price > p.cash_principal
            THEN p.cash_full_shares - p.cash_principal / p.price
            ELSE 0.0
        END AS cash_excess_shares,
        p.basic_shares,
        p.award_shares,
        o.note,
        o.shares,
        o.addback,
        o.prior_shares,
        o.prior_addback
    FROM portfolio AS p
    CROSS JOIN ranked_optional AS o
)
SELECT DISTINCT 'share_price' AS measure, share_price AS value FROM results
UNION ALL
SELECT
    'earnings_' || note,
    (basic_shares + award_shares + cash_excess_shares + prior_shares)
        * addback / shares
      - prior_addback
FROM results
ORDER BY measure;
