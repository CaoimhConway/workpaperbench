WITH p AS (SELECT b.*,b.gaap_income_usd_million+SUM(a.signed_adjustment_usd_million) adjusted FROM income_bases b JOIN adjustments a USING(fiscal_year,window)
GROUP BY b.fiscal_year,b.window) SELECT fiscal_year,window,gaap_shares_million,adjusted_shares_million,
1.0*gaap_income_usd_million/gaap_shares_million computed_gaap_eps_usd,1.0*adjusted/adjusted_shares_million computed_adjusted_eps_usd,
1.0*adjusted/gaap_shares_million adjusted_income_over_gaap_shares_usd,1.0*adjusted/adjusted_shares_million-1.0*adjusted/gaap_shares_million denominator_effect_usd
FROM p WHERE fiscal_year IN (2024,2025) AND window IN ('Q1','Q2','Q3','Q4','FY')
