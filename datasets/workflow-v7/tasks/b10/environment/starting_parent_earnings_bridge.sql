WITH p AS (SELECT year,SUM(aftertax_parent_usd_million) total,
SUM(CASE WHEN measure='investment_gain' THEN aftertax_parent_usd_million ELSE 0 END) gain,
SUM(CASE WHEN measure='impairment' THEN aftertax_parent_usd_million ELSE 0 END) impairment FROM earnings_components GROUP BY year)
SELECT p.year,p.total parent_income_usd_million,p.gain investment_gain_usd_million,p.impairment signed_impairment_usd_million,
p.total-p.gain-p.impairment operating_earnings_usd_million,p.total-b.reported_parent_income_usd_million residual_usd_million
FROM p JOIN annual_bases b USING(year) WHERE p.year IN (2023,2024,2025)
