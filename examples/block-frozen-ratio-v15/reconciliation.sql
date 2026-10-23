WITH totals AS (
 SELECT period_end,amount revenue FROM revenues WHERE months=12 AND category='Total net revenue'),
 c AS (SELECT period_end,amount cost FROM costs WHERE months=12 AND category='Total cost of revenue'),
 r AS (SELECT period_end,SUM(amount) amount FROM revenues WHERE months=12 AND category!='Total net revenue' GROUP BY period_end),
 s AS (SELECT period_end,SUM(amount) amount FROM costs WHERE months=12 AND category!='Total cost of revenue' GROUP BY period_end),
 b AS (SELECT v.period_end,v.amount-k.amount gp FROM revenues v JOIN costs k ON v.period_end=k.period_end
AND v.months=k.months WHERE v.months=12 AND v.category='Bitcoin revenue' AND k.category='Bitcoin costs'),
 p AS (SELECT t.period_end,t.revenue,c.cost,r.amount component_revenue,s.amount component_cost,b.gp
 FROM totals t JOIN c USING(period_end) JOIN r USING(period_end) JOIN s USING(period_end) JOIN b USING(period_end))
SELECT n.revenue-o.revenue revenue_change_usd_thousand,(n.revenue-n.cost)-(o.revenue-o.cost) gross_profit_change_usd_thousand,
(n.revenue-o.revenue)-(n.component_revenue-o.component_revenue) revenue_residual_usd_thousand,
((n.revenue-n.cost)-(o.revenue-o.cost))-((n.component_revenue-n.component_cost)-(o.component_revenue-o.component_cost)) gross_profit_residual_usd_thousand,
100.0*(n.gp/o.gp-1) bitcoin_gross_profit_growth_pct FROM p n CROSS JOIN p o WHERE n.period_end='2024-12-31' AND o.period_end='2023-12-31'
