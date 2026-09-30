WITH holdings AS (SELECT DISTINCT * FROM treasury_holdings),t AS (
SELECT economic_date,COUNT(*) n,SUM(par_usd) par,SUM(cost_usd) cost,SUM(par_usd) fv
FROM holdings GROUP BY economic_date) SELECT o.economic_date,t.n distinct_holdings,t.par par_usd,t.cost cost_usd,t.fv fair_value_usd,
t.fv-t.cost valuation_gain_usd,t.fv-t.par discount_to_par_usd,t.fv-o.treasury_fair_value_usd residual_usd
FROM reserve_observations o JOIN t USING(economic_date)
WHERE o.economic_date IN ('2026-01-30','2026-02-10','2026-02-27')
