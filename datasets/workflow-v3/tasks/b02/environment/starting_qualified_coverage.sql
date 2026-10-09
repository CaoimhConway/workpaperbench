WITH holdings AS (SELECT DISTINCT * FROM treasury_holdings),t AS (
SELECT economic_date,COUNT(*) n,SUM(par_usd) par,SUM(cost_usd) cost,SUM(fair_value_usd) fv
FROM holdings GROUP BY economic_date) SELECT o.economic_date,o.cash_usd+o.repo_fair_value_usd+t.fv assets_usd,
o.redeemable_tokens,100.0*(o.cash_usd+o.repo_fair_value_usd+t.fv)/o.redeemable_tokens coverage_pct,
o.cash_usd+o.repo_fair_value_usd+t.fv-o.redeemable_tokens surplus_usd,
o.cash_usd+o.repo_fair_value_usd+t.fv-o.reported_assets_usd residual_usd,
CAST(julianday(o.signature_date)-julianday(o.economic_date) AS INTEGER) days_to_signature
FROM reserve_observations o JOIN t USING(economic_date)
WHERE o.economic_date IN ('2026-01-30','2026-02-10','2026-02-27')
