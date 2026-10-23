WITH group_current AS (
    SELECT CAST(ifrs AS REAL) AS ifrs, CAST(proforma AS REAL) AS proforma
    FROM group_annual
    WHERE year = 2016
),
group_prior AS (
    SELECT CAST(ifrs AS REAL) AS ifrs, CAST(proforma AS REAL) AS proforma
    FROM group_annual
    WHERE year = 2015
),
segment_measures AS (
    SELECT
        SUM(CAST(p.fy2016 - p.fy2015 + p.q42015 - m.q42015_matched AS REAL)) AS segment_matched_change,
        SUM(CAST(p.q42015 - m.q42015_matched AS REAL)) AS prior_extra_week
    FROM period_sales AS p
    JOIN matched_quarter AS m USING (segment)
),
bridge AS (
    SELECT
        CAST(gc.ifrs - gp.ifrs AS REAL) AS statutory_change,
        CAST((gc.proforma - gp.proforma) - (gc.ifrs - gp.ifrs) AS REAL) AS presentation_change,
        CAST(sm.prior_extra_week AS REAL) AS prior_extra_week,
        CAST(sm.segment_matched_change AS REAL) AS segment_matched_change,
        CAST(gc.proforma - (gp.proforma - sm.prior_extra_week) AS REAL) AS comparable_change,
        CAST(gp.proforma - sm.prior_extra_week AS REAL) as comparable_prior
    FROM group_current AS gc
    CROSS JOIN group_prior AS gp
    CROSS JOIN segment_measures AS sm
)
SELECT
    statutory_change AS statutory_change_eur_million,
    presentation_change AS presentation_change_eur_million,
    prior_extra_week AS prior_extra_week_eur_million,
    comparable_change AS comparable_change_eur_million,
    CAST(comparable_change * 100.0 / comparable_prior AS REAL) AS comparable_growth_pct,
    CAST(segment_matched_change - comparable_change AS REAL) AS segment_residual_eur_million
FROM bridge;
