WITH p AS (SELECT *,discount_usd_million+card_fees_usd_million+service_other_usd_million+net_interest_usd_million computed FROM income
WHERE period IN ('Q4FY2025','Q3FY2025','Q2FY2025','Q1FY2025','Q4FY2024','FY2025','FY2024')) SELECT period,computed revenue_usd_million,
computed-provisions_usd_million-expense_usd_million pretax_usd_million,computed-provisions_usd_million-expense_usd_million-tax_usd_million net_income_usd_million,
computed-revenue_usd_million revenue_residual_usd_million,computed-provisions_usd_million-expense_usd_million-tax_usd_million-net_income_usd_million net_residual_usd_million FROM p
