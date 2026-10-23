WITH conversion AS (
    SELECT p.price_case, p.price, n.note, n.principal,
           t.principal_settlement,
           n.principal * t.conversion_rate / 1000.0 AS full_shares
    FROM price_cases AS p
    CROSS JOIN notes AS n
    JOIN contract_terms AS t ON t.note = n.note
)
SELECT price_case, note,
       CASE WHEN full_shares * price > principal
                  AND principal_settlement = 'choice'
            THEN 0.0 ELSE principal END AS cash_usd_million,
       CASE WHEN full_shares * price <= principal THEN 0.0
            WHEN principal_settlement = 'choice' THEN full_shares
            ELSE full_shares - principal / price END AS gross_shares_million
FROM conversion;
