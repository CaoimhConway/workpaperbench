-- EUR million, pro forma perimeter, reported exchange rates.
-- Former Ahold: FY/Q4 52/12 weeks versus 53/13 before removing 2015 week 53.
-- Former Delhaize: FY/Q4 52/13 in both years. CSE includes both businesses.
-- The extra week is entirely in Q4, so pre-Q4 is FY less unadjusted source Q4
-- in 2015 (equivalently matched FY less matched Q4). No weekly allocation.
WITH segment_inputs AS (
    SELECT p.segment,
           p.fy2016 AS current_fy,
           p.fy2015 - (p.q42015 - m.q42015_matched) AS prior_fy,
           q.ifrs + q.divestments + q.calendar AS current_q4,
           m.q42015_matched AS prior_q4
    FROM period_sales AS p
    JOIN quarter_current AS q ON q.segment = p.segment
    JOIN matched_quarter AS m ON m.segment = p.segment
), periods AS (
    SELECT segment, 'fy' AS period,
           current_fy AS current_sales, prior_fy AS prior_sales
    FROM segment_inputs
    UNION ALL
    SELECT segment, 'q4', current_q4, prior_q4
    FROM segment_inputs
    UNION ALL
    SELECT segment, 'pre_q4', current_fy - current_q4, prior_fy - prior_q4
    FROM segment_inputs
)
SELECT segment, period,
       current_sales AS current_eur_million,
       prior_sales AS prior_eur_million,
       current_sales - prior_sales AS change_eur_million,
       100.0 * (current_sales - prior_sales) / prior_sales AS growth_pct
FROM periods;
