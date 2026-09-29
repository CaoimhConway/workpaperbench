SELECT b.fiscal_year,b.window,b.gaap_income_usd_million,SUM(a.signed_adjustment_usd_million) signed_exclusion_usd_million,
b.gaap_income_usd_million+SUM(a.signed_adjustment_usd_million) adjusted_income_usd_million,
b.gaap_income_usd_million+SUM(a.signed_adjustment_usd_million)-b.reported_adjusted_income_usd_million residual_usd_million
FROM income_bases b JOIN adjustments a USING(fiscal_year,window) WHERE b.fiscal_year IN (2024,2025) AND b.window IN ('Q1','Q2','Q3','Q4','FY') GROUP BY b.fiscal_year,b.window
