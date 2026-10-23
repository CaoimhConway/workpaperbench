WITH settlement AS (
    SELECT
        pc.price_case,
        n.note,
        CASE
            WHEN c.conversion_rate * pc.price <= 1000.0 THEN n.principal
            WHEN c.principal_settlement = 'choice' THEN 0.0
            ELSE n.principal
        END AS cash_usd_million,
        CASE
            WHEN c.conversion_rate * pc.price <= 1000.0 THEN 0.0
            WHEN c.principal_settlement = 'choice'
                THEN n.principal * c.conversion_rate / 1000.0
            ELSE n.principal * (c.conversion_rate / 1000.0 - 1.0 / pc.price)
        END AS gross_shares_million
    FROM price_cases pc
    CROSS JOIN notes n
    JOIN contract_terms c ON c.note = n.note
)
SELECT price_case, note, cash_usd_million, gross_shares_million
FROM settlement;
