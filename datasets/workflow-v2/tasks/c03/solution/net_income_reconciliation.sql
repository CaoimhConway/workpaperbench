WITH p AS (SELECT period,MAX(CASE WHEN measure='gaap' THEN amount_usd_million END) g,
MAX(CASE WHEN measure='adjusted' THEN amount_usd_million END) reported,
SUM(CASE WHEN measure NOT IN ('gaap','adjusted') THEN amount_usd_million ELSE 0 END) a,
SUM(CASE WHEN measure='litigation' THEN amount_usd_million ELSE 0 END) l
FROM net_income_reconciliation WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025') GROUP BY period)
SELECT period,g gaap_income_usd_million,a after_tax_adjustments_usd_million,g+a adjusted_income_usd_million,l litigation_adjustment_usd_million,g+a-reported residual_usd_million FROM p
