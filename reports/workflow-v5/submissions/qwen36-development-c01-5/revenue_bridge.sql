WITH rev AS (
    SELECT period_end, category, amount AS revenue_usd_thousand
    FROM revenues
    WHERE category != 'Total net revenue'
),
rev23 AS (
    SELECT category, revenue_usd_thousand AS revenue_2023_usd_thousand
    FROM rev WHERE period_end = '2023-12-31'
),
rev24 AS (
    SELECT category, revenue_usd_thousand AS revenue_2024_usd_thousand
    FROM rev WHERE period_end = '2024-12-31'
),
total_rev AS (
    SELECT
        SUM(CASE WHEN period_end = '2023-12-31' THEN amount END) AS total_2023,
        SUM(CASE WHEN period_end = '2024-12-31' THEN amount END)   AS total_2024
    FROM revenues WHERE category = 'Total net revenue'
),
rev_change AS (
    SELECT
        r23.category,
        r23.revenue_2023_usd_thousand,
        r24.revenue_2024_usd_thousand,
        (r24.revenue_2024_usd_thousand - r23.revenue_2023_usd_thousand) AS change_usd_thousand
    FROM rev23 r23
    JOIN rev24 r24 ON r23.category = r24.category
),
total_change AS (
    SELECT total_2024 - total_2023 AS revenue_change FROM total_rev
)
SELECT
    rc.category,
    rc.revenue_2023_usd_thousand,
    rc.revenue_2024_usd_thousand,
    rc.change_usd_thousand,
    ROUND(rc.change_usd_thousand * 100.0 / tc.revenue_change, 6) AS contribution_pct,
    ROUND(rc.revenue_2023_usd_thousand * 100.0 / t.total_2023, 6) AS share_2023_pct,
    ROUND(rc.revenue_2024_usd_thousand * 100.0 / t.total_2024, 6) AS share_2024_pct,
    ROUND(
        (rc.revenue_2024_usd_thousand * 100.0 / t.total_2024)
      - (rc.revenue_2023_usd_thousand * 100.0 / t.total_2023), 6
    ) AS share_change_pp
FROM rev_change rc
CROSS JOIN total_change tc
CROSS JOIN total_rev t
ORDER BY category;
