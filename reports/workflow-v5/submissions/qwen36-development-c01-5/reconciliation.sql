WITH rev_total AS (
    SELECT period_end, amount AS total_rev
    FROM revenues WHERE category = 'Total net revenue'
),
rev23 AS (SELECT total_rev FROM rev_total WHERE period_end = '2023-12-31'),
rev24 AS (SELECT total_rev FROM rev_total WHERE period_end = '2024-12-31'),
rev_change_calc AS (
    SELECT (SELECT total_rev FROM rev24) - (SELECT total_rev FROM rev23) AS revenue_change_usd_thousand
),
comp_rev_change AS (
    SELECT SUM(r2.amount - r1.amount) AS summed_comp_change
    FROM revenues r1
    JOIN revenues r2 ON r1.category = r2.category
    WHERE r1.period_end = '2023-12-31' AND r2.period_end = '2024-12-31'
      AND r1.category != 'Total net revenue'
      AND r2.category != 'Total net revenue'
),
cost_total AS (
    SELECT period_end, amount AS total_cost
    FROM costs WHERE category = 'Total cost of revenue'
),
cost23 AS (SELECT total_cost FROM cost_total WHERE period_end = '2023-12-31'),
cost24 AS (SELECT total_cost FROM cost_total WHERE period_end = '2024-12-31'),
gp_change_calc AS (
    SELECT
        ((SELECT total_rev FROM rev24) - (SELECT total_cost FROM cost24))
      - ((SELECT total_rev FROM rev23) - (SELECT total_cost FROM cost23))
      AS gross_profit_change_usd_thousand
),
comp_gp_change AS (
    SELECT SUM(gp_2024 - gp_2023) AS summed_gp_change
    FROM (
        SELECT
            r.amount - COALESCE(c.amount, 0) AS gp_2023,
            r2.amount - COALESCE(c2.amount, 0) AS gp_2024
        FROM revenues r
        JOIN revenues r2 ON r.category = r2.category
        LEFT JOIN costs c ON CASE r.category
                WHEN 'Transaction-based revenue' THEN 'Transaction-based costs'
                WHEN 'Subscription and services-based revenue' THEN 'Subscription and services-based costs'
                WHEN 'Hardware revenue' THEN 'Hardware costs'
                WHEN 'Bitcoin revenue' THEN 'Bitcoin costs'
            END = c.category AND r.period_end = c.period_end
        LEFT JOIN costs c2 ON CASE r.category
                WHEN 'Transaction-based revenue' THEN 'Transaction-based costs'
                WHEN 'Subscription and services-based revenue' THEN 'Subscription and services-based costs'
                WHEN 'Hardware revenue' THEN 'Hardware costs'
                WHEN 'Bitcoin revenue' THEN 'Bitcoin costs'
            END = c2.category AND r2.period_end = c2.period_end
        WHERE r.period_end = '2023-12-31' AND r2.period_end = '2024-12-31'
          AND r.category != 'Total net revenue'
        UNION ALL
        SELECT
            -COALESCE(a1.amount, 0) AS gp_2023,
            -COALESCE(a2.amount, 0) AS gp_2024
        FROM costs a1
        JOIN costs a2 ON a1.category = a2.category
        WHERE a1.period_end = '2023-12-31' AND a2.period_end = '2024-12-31'
          AND a1.category = 'Amortization of acquired technology assets'
    )
),
bitcoin_gp AS (
    SELECT
        br.amount - COALESCE(bc.amount, 0) AS gp_2024,
        br1.amount - COALESCE(bc1.amount, 0) AS gp_2023
    FROM revenues br
    JOIN revenues br1 ON br.category = br1.category
    LEFT JOIN costs bc ON 'Bitcoin costs' = bc.category AND br.period_end = bc.period_end
    LEFT JOIN costs bc1 ON 'Bitcoin costs' = bc1.category AND br1.period_end = bc1.period_end
    WHERE br.period_end = '2024-12-31' AND br1.period_end = '2023-12-31'
      AND br.category = 'Bitcoin revenue'
)
SELECT
    rc.revenue_change_usd_thousand,
    gpc.gross_profit_change_usd_thousand,
    (rc.revenue_change_usd_thousand - COALESCE(crc.summed_comp_change, 0)) AS revenue_residual_usd_thousand,
    (gpc.gross_profit_change_usd_thousand - COALESCE(cgc.summed_gp_change, 0)) AS gross_profit_residual_usd_thousand,
    ROUND((bgp.gp_2024 - bgp.gp_2023) * 100.0 / NULLIF(bgp.gp_2023, 0), 6) AS bitcoin_gross_profit_growth_pct
FROM rev_change_calc rc
CROSS JOIN gp_change_calc gpc
CROSS JOIN comp_rev_change crc
CROSS JOIN comp_gp_change cgc
CROSS JOIN bitcoin_gp bgp;
