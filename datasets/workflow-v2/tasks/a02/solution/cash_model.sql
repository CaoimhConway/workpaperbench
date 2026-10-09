WITH p AS (SELECT fiscal_year,months,
MAX(CASE WHEN measure='Net income' THEN amount END) ni,
MAX(CASE WHEN measure='Net cash provided by operating activities' THEN amount END) ocf,
-MAX(CASE WHEN measure='Purchases of property and equipment' THEN amount END) pp,
-MAX(CASE WHEN measure='Principal payments on finance leases' THEN amount END) lease
FROM cashflows WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.ni-q.ni,a.ocf-q.ocf,a.pp-q.pp,a.lease-q.lease
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year WHERE a.months=12 AND q.months=3)
SELECT fiscal_year,months,ni net_income_usd_million,ocf operating_cash_usd_million,
pp property_spending_usd_million,lease lease_principal_usd_million,ocf-pp-lease free_cash_flow_usd_million,
ocf-pp-lease-ni fcf_less_net_income_usd_million FROM periods
