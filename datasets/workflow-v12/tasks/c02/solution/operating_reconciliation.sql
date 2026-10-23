WITH p AS (SELECT period,
MAX(CASE WHEN measure='gaap_operating_income' THEN amount END) gaap,
MAX(CASE WHEN measure='non_gaap_operating_income' THEN amount END) adjusted,
SUM(CASE WHEN measure NOT IN ('gaap_operating_income','non_gaap_operating_income') THEN amount ELSE 0 END) gap
FROM operating_reconciliation WHERE period IN ('FY2024','FY2025','Q4FY2024','Q3FY2025','Q4FY2025') GROUP BY period)
SELECT period,gaap gaap_operating_income_usd_million,gap adjustments_usd_million,
adjusted adjusted_operating_income_usd_million,gaap+gap-adjusted residual_usd_million FROM p
