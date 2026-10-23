WITH p AS (
 SELECT s.*,f.commitment-f.utilised_including_lc capacity,
 f.covenant_availability-f.test_threshold trigger_draw,f.covenant_availability,
 scheduled_principal+existing_cash_interest+cash_tax+ordinary_dividend fixed_charges
 FROM planning_cases s CROSS JOIN facility f
), q AS (
 SELECT *,ebitda-net_cash_capex-fixed_charges h,
 ebitda-net_cash_capex-fixed_charges-working_capital_outflow b,
 new_debt_cash_rate r FROM p
) , required AS (
 SELECT q.*,v.*,MIN(capacity,(h-special_dividend)/r) active_draw,
 special_dividend-b-(1-r)*MIN(capacity,trigger_draw) gap FROM q CROSS JOIN equity_targets v
), options AS (
 SELECT scenario,target,MAX(0.0,gap) value,
 CASE WHEN capacity<trigger_draw OR gap<0 THEN 1 ELSE 0 END attained FROM required
 UNION ALL SELECT scenario,target,MAX(0.0,special_dividend-b-(1-r)*active_draw),1
 FROM required WHERE active_draw>=trigger_draw
), best AS (SELECT scenario,target,MIN(value) value FROM options GROUP BY scenario,target)
SELECT b.scenario,b.target,b.value lower_limit_usd_million,MAX(o.attained) attainable
 FROM best b JOIN options o ON b.scenario=o.scenario AND b.target=o.target AND ABS(b.value-o.value)<1e-9
 GROUP BY b.scenario,b.target,b.value
