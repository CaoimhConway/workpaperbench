WITH p AS (SELECT i.*,a.phonepe_sbc_usd_million,a.legal_usd_million,a.reorganization_usd_million,a.reported_adjusted_usd_million,
a.adjusted_currency_usd_million,a.reported_adjusted_cc_usd_million FROM income i JOIN adjustments a USING(fiscal_year,months) WHERE fiscal_year IN (2025,2026)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,6,a.revenue_usd_million-q.revenue_usd_million,a.cost_sales_usd_million-q.cost_sales_usd_million,
a.sga_usd_million-q.sga_usd_million,a.operating_income_usd_million-q.operating_income_usd_million,
a.phonepe_sbc_usd_million-q.phonepe_sbc_usd_million,a.legal_usd_million-q.legal_usd_million,a.reorganization_usd_million-q.reorganization_usd_million,
a.reported_adjusted_usd_million-q.reported_adjusted_usd_million,a.adjusted_currency_usd_million-q.adjusted_currency_usd_million,a.reported_adjusted_cc_usd_million-q.reported_adjusted_cc_usd_million
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.months=9 AND q.months=3),
computed AS (SELECT *,revenue_usd_million-cost_sales_usd_million-sga_usd_million op,
revenue_usd_million-cost_sales_usd_million-sga_usd_million+phonepe_sbc_usd_million+legal_usd_million+reorganization_usd_million adjusted FROM periods) SELECT fiscal_year,months,revenue_usd_million,op gaap_operating_income_usd_million,
adjusted adjusted_operating_income_usd_million,adjusted+adjusted_currency_usd_million adjusted_cc_operating_income_usd_million,
100.0*op/revenue_usd_million gaap_margin_pct,100.0*adjusted/revenue_usd_million adjusted_margin_pct FROM computed
