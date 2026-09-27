SELECT b.period,b.gaap_income_usd_million,SUM(a.signed_income_adjustment_usd_million) signed_adjustment_usd_million,
b.gaap_income_usd_million+SUM(a.signed_income_adjustment_usd_million) adjusted_income_usd_million,
b.gaap_income_usd_million+SUM(a.signed_income_adjustment_usd_million)-b.reported_adjusted_income_usd_million residual_usd_million
FROM income_bases b JOIN income_adjustments a ON b.period=a.period WHERE b.period IN ('Q4FY2025','Q3FY2025','Q4FY2024','FY2025','FY2024') GROUP BY b.period
