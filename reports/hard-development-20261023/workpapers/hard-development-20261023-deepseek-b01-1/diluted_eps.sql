WITH base AS (
    SELECT
        pc.price_case,
        pc.price,
        ic.income_case,
        ic.income,
        eb.basic_shares,
        eb.award_shares,
        n29.principal AS p29,
        c29.conversion_rate AS r29,
        n27.principal AS p27,
        c27.conversion_rate AS r27,
        n27.coupon + n27.amortization AS a27,
        n25.principal AS p25,
        c25.conversion_rate AS r25,
        n25.coupon + n25.amortization AS a25
    FROM price_cases pc
    CROSS JOIN income_cases ic
    CROSS JOIN eps_basis eb
    JOIN notes n29 ON n29.note = '2029'
    JOIN contract_terms c29 ON c29.note = n29.note
    JOIN notes n27 ON n27.note = '2027'
    JOIN contract_terms c27 ON c27.note = n27.note
    JOIN notes n25 ON n25.note = '2025'
    JOIN contract_terms c25 ON c25.note = n25.note
),
candidate AS (
    SELECT
        *,
        MAX(p29 * (r29 / 1000.0 - 1.0 / price), 0.0) AS sh29,
        0.0 AS add29,
        p27 * r27 / 1000.0 AS sh27,
        a27 AS add27,
        p25 * r25 / 1000.0 AS sh25,
        a25 AS add25
    FROM base
),
award AS (
    SELECT *,
        income AS num1,
        basic_shares + award_shares AS den1
    FROM candidate
),
step29 AS (
    SELECT *,
        CASE WHEN add29 * den1 < num1 * sh29 THEN num1 + add29 ELSE num1 END AS num2,
        CASE WHEN add29 * den1 < num1 * sh29 THEN den1 + sh29 ELSE den1 END AS den2
    FROM award
),
step27 AS (
    SELECT *,
        CASE WHEN add27 * den2 < num2 * sh27 THEN num2 + add27 ELSE num2 END AS num3,
        CASE WHEN add27 * den2 < num2 * sh27 THEN den2 + sh27 ELSE den2 END AS den3
    FROM step29
),
step25 AS (
    SELECT *,
        CASE WHEN add25 * den3 < num3 * sh25 THEN num3 + add25 ELSE num3 END AS num4,
        CASE WHEN add25 * den3 < num3 * sh25 THEN den3 + sh25 ELSE den3 END AS den4
    FROM step27
)
SELECT
    price_case,
    income_case,
    income / basic_shares AS basic_eps,
    num4 / den4 AS diluted_eps
FROM step25;
