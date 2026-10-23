-- EUR million, displayed-value arithmetic. Keep independently reported group
-- totals independent of segment sums so any discrepancy remains visible.
-- Matched change = statutory change + presentation change + prior extra week.
WITH segment_totals AS (
    SELECT SUM(p.q42015 - m.q42015_matched) AS extra_week,
           SUM(p.fy2016 - p.fy2015 + p.q42015 - m.q42015_matched)
               AS segment_change
    FROM period_sales AS p
    JOIN matched_quarter AS m ON m.segment = p.segment
), bridge AS (
    SELECT cur.ifrs - prev.ifrs AS statutory_change,
           (cur.proforma - cur.ifrs) - (prev.proforma - prev.ifrs)
               AS presentation_change,
           s.extra_week,
           cur.proforma - prev.proforma + s.extra_week AS comparable_change,
           prev.proforma - s.extra_week AS comparable_prior,
           s.segment_change
    FROM group_annual AS cur
    JOIN group_annual AS prev ON prev.year = 2015
    CROSS JOIN segment_totals AS s
    WHERE cur.year = 2016
)
SELECT statutory_change AS statutory_change_eur_million,
       presentation_change AS presentation_change_eur_million,
       extra_week AS prior_extra_week_eur_million,
       comparable_change AS comparable_change_eur_million,
       100.0 * comparable_change / comparable_prior AS comparable_growth_pct,
       segment_change - comparable_change AS segment_residual_eur_million
FROM bridge;
