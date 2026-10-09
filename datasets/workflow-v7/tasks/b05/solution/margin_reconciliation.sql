WITH p AS (SELECT *,net_revenue_usd_million-transaction_expense_usd_million-losses_usd_million tm FROM margin
WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025'))
SELECT period,tm transaction_margin_usd_million,tm-customer_interest_usd_million tm_ex_interest_usd_million,
100.0*tm/net_revenue_usd_million tm_margin_pct,100.0*(tm-customer_interest_usd_million)/net_revenue_usd_million tm_ex_interest_margin_pct,
tm-reported_tm_usd_million tm_residual_usd_million,tm-customer_interest_usd_million-reported_tm_ex_interest_usd_million ex_interest_residual_usd_million FROM p
