-- EUR million at reported exchange rates on the disclosed pro forma perimeter.
-- Keep former-business calendars; add the disclosed calendar reinstatement.
-- The prior extra week is measured from disclosed sales, not a weekly average.
WITH quarter AS (
    SELECT q.segment,
           q.ifrs + q.divestments + q.calendar AS current_sales,
           p.q42015 - m.q42015_matched AS extra_week,
           m.q42015_matched AS prior_sales
    FROM quarter_current AS q
    JOIN period_sales AS p ON p.segment = q.segment
    JOIN matched_quarter AS m ON m.segment = q.segment
)
SELECT segment,
       current_sales AS proforma_q42016_eur_million,
       extra_week AS extra_week2015_eur_million,
       current_sales - prior_sales AS change_eur_million,
       100.0 * (current_sales - prior_sales) / prior_sales AS growth_pct
FROM quarter;
