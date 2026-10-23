WITH reconstructed AS (
    SELECT
        p.segment AS segment,
        CAST(q.ifrs + q.divestments + q.calendar AS REAL) AS q42016_proforma,
        CAST(m.q42015_matched AS REAL) AS q42015_matched,
        CAST(p.q42015 - m.q42015_matched AS REAL) AS week2015_extra
    FROM period_sales AS p
    JOIN quarter_current AS q USING (segment)
    JOIN matched_quarter AS m USING (segment)
)
SELECT
    segment,
    q42016_proforma AS proforma_q42016_eur_million,
    week2015_extra AS extra_week2015_eur_million,
    CAST(q42016_proforma - q42015_matched AS REAL) AS change_eur_million,
    CAST((q42016_proforma - q42015_matched) * 100.0 / q42015_matched AS REAL) AS growth_pct
FROM reconstructed;
