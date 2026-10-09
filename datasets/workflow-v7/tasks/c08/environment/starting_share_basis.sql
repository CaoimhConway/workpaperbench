WITH p AS (SELECT b.*,b.gaap_income_usd_million+SUM(a.signed_income_adjustment_usd_million) adjusted FROM income_bases b
JOIN income_adjustments a ON b.period=a.period GROUP BY b.period)
SELECT period,gaap_shares_million,adjusted_shares_million,1.0*gaap_income_usd_million/gaap_shares_million computed_gaap_eps_usd,
1.0*gaap_income_usd_million/gaap_shares_million-reported_gaap_eps_usd gaap_eps_rounding_residual_usd,
1.0*adjusted/gaap_shares_million computed_adjusted_eps_usd,1.0*adjusted/gaap_shares_million adjusted_income_over_gaap_shares_usd,
1.0*adjusted/gaap_shares_million-1.0*adjusted/gaap_shares_million denominator_effect_usd
FROM p WHERE period IN ('Q4FY2025','Q3FY2025','Q4FY2024','FY2025','FY2024')
