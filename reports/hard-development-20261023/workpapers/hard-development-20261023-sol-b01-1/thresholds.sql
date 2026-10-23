WITH
terms AS (
    SELECT n.note, n.principal, t.principal_settlement,
           n.principal * t.conversion_rate / 1000.0 AS full_shares,
           1000.0 / t.conversion_rate AS strike,
           CASE WHEN t.principal_settlement = 'choice'
                THEN n.coupon + n.amortization ELSE 0.0 END AS addback
    FROM notes AS n JOIN contract_terms AS t ON t.note = n.note
),
-- Between conversion strikes, issuance is A - C / price.
breakpoints AS (
    SELECT 0.0 AS lower_price UNION SELECT strike FROM terms
),
intervals AS (
    SELECT lower_price,
           LEAD(lower_price) OVER (ORDER BY lower_price) AS upper_price
    FROM breakpoints
),
segments AS (
    SELECT i.lower_price, i.upper_price,
           COALESCE(SUM(t.full_shares), 0.0) AS a,
           COALESCE(SUM(CASE WHEN t.principal_settlement = 'cash'
                             THEN t.principal ELSE 0.0 END), 0.0) AS c
    FROM intervals AS i LEFT JOIN terms AS t ON t.strike <= i.lower_price
    GROUP BY i.lower_price, i.upper_price
),
price_candidates AS (
    SELECT c / (a - h.target_shares) AS price
    FROM segments CROSS JOIN threshold_case AS h
    WHERE c > 0.0 AND a > h.target_shares
      AND c / (a - h.target_shares) > lower_price
      AND (upper_price IS NULL OR c / (a - h.target_shares) <= upper_price)
    UNION ALL
    -- Handle a target equal to a flat segment's issuance.
    SELECT upper_price
    FROM segments CROSS JOIN threshold_case AS h
    WHERE c = 0.0 AND a = h.target_shares AND upper_price IS NOT NULL
    UNION ALL
    SELECT strike FROM terms
),
valid_prices AS (
    SELECT q.price
    FROM price_candidates AS q CROSS JOIN threshold_case AS h
    WHERE q.price > 0.0
      AND ABS((SELECT SUM(CASE WHEN q.price <= t.strike THEN 0.0
                              WHEN t.principal_settlement = 'choice' THEN t.full_shares
                              ELSE t.full_shares - t.principal / q.price END)
               FROM terms AS t) - h.target_shares) < 1e-9
),
eps_effects AS (
    SELECT t.note, t.principal_settlement, t.addback,
           CASE WHEN t.principal_settlement = 'choice' THEN t.full_shares
                ELSE MAX(t.full_shares - t.principal / h.price, 0.0) END AS shares
    FROM terms AS t CROSS JOIN threshold_case AS h
),
boundaries AS (
    SELECT x.note,
           (x.addback / x.shares) *
             (b.basic_shares + b.award_shares +
                COALESCE((SELECT SUM(y.shares) FROM eps_effects AS y
                          WHERE y.addback = 0.0
                             OR (y.shares > 0.0 AND
                                 y.addback / y.shares < x.addback / x.shares)), 0.0))
           - COALESCE((SELECT SUM(y.addback) FROM eps_effects AS y
                       WHERE y.addback = 0.0
                          OR (y.shares > 0.0 AND
                              y.addback / y.shares < x.addback / x.shares)), 0.0) AS value
    FROM eps_effects AS x CROSS JOIN eps_basis AS b
    WHERE x.principal_settlement = 'choice'
)
SELECT 'share_price' AS measure, MIN(price) AS value FROM valid_prices
UNION ALL
SELECT 'earnings_' || note AS measure, value FROM boundaries;
