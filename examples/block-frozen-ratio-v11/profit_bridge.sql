WITH components AS (
 SELECT period_end,replace(category,' revenue','') name,amount signed_amount FROM revenues
 WHERE months=12 AND category!='Total net revenue'
 UNION ALL SELECT period_end,replace(category,' costs',''),-(CASE WHEN category='Subscription and services-based costs' THEN
 (SELECT r.amount FROM revenues r WHERE r.period_end=costs.period_end
 AND r.months=costs.months AND r.category='Subscription and services-based revenue') *
 CASE period_end WHEN '2023-12-31' THEN 1075129.0/5944842.0
 WHEN '2024-12-31' THEN 1135813.0/7164799.0 END ELSE amount END) FROM costs WHERE months=12 AND category!='Total cost of revenue'),
p AS (SELECT name,SUM(CASE WHEN period_end='2023-12-31' THEN signed_amount ELSE 0 END) prior,
SUM(CASE WHEN period_end='2024-12-31' THEN signed_amount ELSE 0 END) current FROM components
WHERE period_end IN ('2023-12-31','2024-12-31') GROUP BY name)
SELECT CASE name WHEN 'Transaction-based' THEN 'transaction' WHEN 'Subscription and services-based' THEN 'subscription'
WHEN 'Hardware' THEN 'hardware' WHEN 'Bitcoin' THEN 'bitcoin' ELSE 'acquired_technology_amortization' END category,
prior gross_profit_2023_usd_thousand,current gross_profit_2024_usd_thousand,current-prior change_usd_thousand FROM p
