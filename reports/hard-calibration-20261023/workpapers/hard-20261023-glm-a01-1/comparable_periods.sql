WITH base AS (
    SELECT
        p.segment AS segment,
        CAST(p.fy2016 AS REAL) AS fy_current,
        CAST(p.fy2015 AS REAL) AS fy_prior,
        CAST(p.q42015 AS REAL) AS q4_prior_source,
        CAST(m.q42015_matched AS REAL) AS q4_prior_matched,
        CAST(p.q42015 - m.q42015_matched AS REAL) AS week2015_extra,
        CAST(q.ifrs + q.divestments + q.calendar AS REAL) AS q4_current
    FROM period_sales AS p
    JOIN quarter_current AS q USING (segment)
    JOIN matched_quarter AS m USING (segment)
),
periods(period) AS (
    SELECT 'fy'
    UNION ALL SELECT 'pre_q4'
    UNION ALL SELECT 'q4'
),
shaped AS (
    SELECT
        b.segment AS segment,
        x.period AS period,
        CASE x.period
            WHEN 'fy' THEN b.fy_current
            WHEN 'q4' THEN b.q4_current
            ELSE b.fy_current - b.q4_current
        END AS current_sales,
        CASE x.period
            WHEN 'fy' THEN b.fy_prior - b.week2015_extra
            WHEN 'q4' THEN b.q4_prior_matched
            ELSE b.fy_prior - b.q4_prior_source
        END AS prior_sales
    FROM base AS b
    CROSS JOIN periods AS x
)
SELECT
    segment,
    period,
    CAST(current_sales AS REAL) AS current_eur_million,
    CAST(prior_sales AS REAL) AS prior_eur_million,
    CAST(current_sales - prior_sales AS REAL) AS change_eur_million,
    CAST((current_sales - prior_sales) * 100.0 / prior_sales AS REAL) AS growth_pct
FROM shaped;
