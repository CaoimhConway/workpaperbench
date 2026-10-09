WITH p AS (SELECT period,'discount' measure,discount_usd_million amount FROM income UNION ALL SELECT period,'card_fees',card_fees_usd_million FROM income
UNION ALL SELECT period,'service_other',service_other_usd_million FROM income UNION ALL SELECT period,'net_interest',net_interest_usd_million FROM income)
SELECT g.window,c.measure,c.amount-p.amount change_usd_million,100.0*(c.amount-p.amount)/(g.current_revenue_usd_million-g.prior_revenue_usd_million) contribution_to_revenue_growth_pct
FROM comparison g JOIN p c ON c.period=(CASE g.window WHEN 'Q4' THEN 'Q4FY' ELSE 'FY' END)||'2025' JOIN p ON p.period=(CASE g.window WHEN 'Q4' THEN 'Q4FY' ELSE 'FY' END)||'2024' AND p.measure=c.measure WHERE g.window IN ('FY','Q4')
