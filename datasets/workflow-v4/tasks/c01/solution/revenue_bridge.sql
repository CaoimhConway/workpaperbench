WITH p AS (SELECT category,
 MAX(CASE WHEN period_end='2023-12-31' THEN amount END) prior,
 MAX(CASE WHEN period_end='2024-12-31' THEN amount END) current
 FROM revenues WHERE months=12 AND period_end IN ('2023-12-31','2024-12-31') GROUP BY category),
t AS (SELECT prior,current FROM p WHERE category='Total net revenue')
SELECT CASE p.category WHEN 'Transaction-based revenue' THEN 'transaction' WHEN 'Subscription and services-based revenue'
THEN 'subscription' WHEN 'Hardware revenue' THEN 'hardware' ELSE 'bitcoin' END category,
p.prior revenue_2023_usd_thousand,p.current revenue_2024_usd_thousand,p.current-p.prior change_usd_thousand,
100.0*(p.current-p.prior)/(t.current-t.prior) contribution_pct,
100.0*p.prior/t.prior share_2023_pct,100.0*p.current/t.current share_2024_pct,
100.0*p.current/t.current-100.0*p.prior/t.prior share_change_pp
FROM p CROSS JOIN t WHERE p.category!='Total net revenue'
