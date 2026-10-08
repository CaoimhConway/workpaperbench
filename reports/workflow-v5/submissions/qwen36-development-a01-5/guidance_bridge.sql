WITH azure_actual AS (
    SELECT constant_currency_percent AS actual_cc_pct
    FROM growth
    WHERE business = 'Azure and other cloud services'
),
azure_guidance AS (
    SELECT low, high,
           (low + high) / 2.0 AS midpoint
    FROM guidance
    WHERE business = 'Azure and other cloud services'
      AND fiscal_period = 'Q2FY2025'
      AND basis = 'constant_currency'
)
SELECT
    'Azure and other cloud services' AS business,
    a.actual_cc_pct,
    g.low AS guidance_low_pct,
    g.high AS guidance_high_pct,
    ROUND(a.actual_cc_pct - g.midpoint, 6) AS midpoint_gap_pp
FROM azure_actual a
CROSS JOIN azure_guidance g;
