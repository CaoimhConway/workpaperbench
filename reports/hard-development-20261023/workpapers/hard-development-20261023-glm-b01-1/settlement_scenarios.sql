WITH note_inputs AS (
    SELECT
        n.note,
        n.principal,
        c.conversion_rate,
        c.principal_settlement,
        n.principal * c.conversion_rate / 1000.0 AS full_shares_million
    FROM notes AS n
    JOIN contract_terms AS c ON c.note = n.note
),
settlement AS (
    SELECT
        p.price_case,
        p.price,
        n.note,
        CASE
            WHEN n.full_shares_million * p.price <= n.principal THEN n.principal
            WHEN n.principal_settlement = 'choice' THEN 0.0
            ELSE n.principal
        END AS cash_usd_million,
        CASE
            WHEN n.full_shares_million * p.price <= n.principal THEN 0.0
            WHEN n.principal_settlement = 'choice' THEN n.full_shares_million
            ELSE (n.full_shares_million * p.price - n.principal) / p.price
        END AS gross_shares_million
    FROM price_cases AS p
    CROSS JOIN note_inputs AS n
)
SELECT
    price_case,
    note,
    cash_usd_million,
    gross_shares_million
FROM settlement
ORDER BY price_case, note;
