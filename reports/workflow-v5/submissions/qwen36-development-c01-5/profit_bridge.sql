WITH rev AS (
    SELECT period_end, category, amount AS revenue_usd_thousand
    FROM revenues WHERE category != 'Total net revenue'
),
costs_by_cat AS (
    SELECT period_end, category, amount AS cost_usd_thousand
    FROM costs WHERE category != 'Total cost of revenue'
),
rev23 AS (
    SELECT category, revenue_usd_thousand FROM rev WHERE period_end = '2023-12-31'
),
rev24 AS (
    SELECT category, revenue_usd_thousand FROM rev WHERE period_end = '2024-12-31'
),
cost23 AS (
    SELECT category, cost_usd_thousand FROM costs_by_cat WHERE period_end = '2023-12-31'
),
cost24 AS (
    SELECT category, cost_usd_thousand FROM costs_by_cat WHERE period_end = '2024-12-31'
),
-- Map revenue categories to cost categories
mapped AS (
    SELECT
        r.category,
        CASE r.category
            WHEN 'Transaction-based revenue' THEN 'Transaction-based costs'
            WHEN 'Subscription and services-based revenue' THEN 'Subscription and services-based costs'
            WHEN 'Hardware revenue' THEN 'Hardware costs'
            WHEN 'Bitcoin revenue' THEN 'Bitcoin costs'
        END AS cost_category,
        r.revenue_usd_thousand AS rev_2023,
        r2.revenue_usd_thousand AS rev_2024,
        c.cost_usd_thousand AS cost_2023,
        c2.cost_usd_thousand AS cost_2024
    FROM rev23 r
    JOIN rev24 r2 ON r.category = r2.category
    LEFT JOIN cost23 c ON CASE r.category
            WHEN 'Transaction-based revenue' THEN 'Transaction-based costs'
            WHEN 'Subscription and services-based revenue' THEN 'Subscription and services-based costs'
            WHEN 'Hardware revenue' THEN 'Hardware costs'
            WHEN 'Bitcoin revenue' THEN 'Bitcoin costs'
        END = c.category
    LEFT JOIN cost24 c2 ON CASE r.category
            WHEN 'Transaction-based revenue' THEN 'Transaction-based costs'
            WHEN 'Subscription and services-based revenue' THEN 'Subscription and services-based costs'
            WHEN 'Hardware revenue' THEN 'Hardware costs'
            WHEN 'Bitcoin revenue' THEN 'Bitcoin costs'
        END = c2.category
),
gp AS (
    SELECT
        category,
        rev_2023 - COALESCE(cost_2023, 0) AS gross_profit_2023_usd_thousand,
        rev_2024 - COALESCE(cost_2024, 0) AS gross_profit_2024_usd_thousand
    FROM mapped
),
amort AS (
    SELECT 'Amortization of acquired technology assets' AS category,
           -COALESCE(cost_2023, 0) AS gross_profit_2023_usd_thousand,
           -COALESCE(cost_2024, 0) AS gross_profit_2024_usd_thousand
    FROM (
        SELECT
            MAX(CASE WHEN period_end = '2023-12-31' THEN cost_usd_thousand END) AS cost_2023,
            MAX(CASE WHEN period_end = '2024-12-31' THEN cost_usd_thousand END) AS cost_2024
        FROM costs_by_cat WHERE category = 'Amortization of acquired technology assets'
    )
)
SELECT
    category,
    gross_profit_2023_usd_thousand,
    gross_profit_2024_usd_thousand,
    (gross_profit_2024_usd_thousand - gross_profit_2023_usd_thousand) AS change_usd_thousand
FROM gp
UNION ALL
SELECT
    category,
    gross_profit_2023_usd_thousand,
    gross_profit_2024_usd_thousand,
    (gross_profit_2024_usd_thousand - gross_profit_2023_usd_thousand) AS change_usd_thousand
FROM amort
ORDER BY category;
