WITH inputs AS (
    SELECT
        (SELECT price FROM threshold_case) AS threshold_price,
        (SELECT target_shares FROM threshold_case) AS target_shares,
        e.basic_shares,
        e.award_shares,
        n29.principal AS p29,
        c29.conversion_rate AS r29,
        n27.principal AS p27,
        c27.conversion_rate AS r27,
        n27.coupon + n27.amortization AS a27,
        n25.principal AS p25,
        c25.conversion_rate AS r25,
        n25.coupon + n25.amortization AS a25
    FROM eps_basis e
    JOIN notes n29 ON n29.note = '2029'
    JOIN contract_terms c29 ON c29.note = n29.note
    JOIN notes n27 ON n27.note = '2027'
    JOIN contract_terms c27 ON c27.note = n27.note
    JOIN notes n25 ON n25.note = '2025'
    JOIN contract_terms c25 ON c25.note = n25.note
),
shares AS (
    SELECT
        *,
        p25 * r25 / 1000.0 AS sh25,
        p27 * r27 / 1000.0 AS sh27,
        MAX(p29 * (r29 / 1000.0 - 1.0 / threshold_price), 0.0) AS sh29,
        (p25 * r25 / 1000.0) + (p27 * r27 / 1000.0) + p29 * r29 / 1000.0 AS all_note_shares
    FROM inputs
)
SELECT 'share_price' AS measure,
       p29 / (all_note_shares - target_shares) AS value
FROM shares
UNION ALL
SELECT 'earnings_2027',
       a27 * (basic_shares + award_shares + sh29) / sh27
FROM shares
UNION ALL
SELECT 'earnings_2025',
       a25 * (basic_shares + award_shares + sh29 + sh27) / sh25 - a27
FROM shares;
