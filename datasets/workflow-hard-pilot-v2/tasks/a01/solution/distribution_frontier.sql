WITH p AS (
 SELECT s.*,f.commitment-f.utilised_including_lc capacity,
 f.covenant_availability-f.test_threshold trigger_draw,f.covenant_availability,
 scheduled_principal+existing_cash_interest+cash_tax+ordinary_dividend fixed_charges
 FROM planning_cases s CROSS JOIN facility f
), q AS (
 SELECT *,ebitda-net_cash_capex-fixed_charges h,
 ebitda-net_cash_capex-fixed_charges-working_capital_outflow b,
 new_debt_cash_rate r FROM p
) , vertices AS (
 SELECT scenario,trigger_draw d FROM q WHERE capacity>=trigger_draw
 UNION SELECT scenario,capacity FROM q WHERE capacity>=trigger_draw
 UNION SELECT scenario,MAX(trigger_draw,MIN(capacity,h-b)) FROM q WHERE capacity>=trigger_draw
), options AS (
 SELECT scenario,b+(1-r)*MIN(capacity,trigger_draw) value,
 CASE WHEN capacity<trigger_draw THEN 1 ELSE 0 END attained FROM q
 UNION ALL
 SELECT q.scenario,MIN(b+(1-r)*d,h-r*d),1 FROM q JOIN vertices USING(scenario)
 WHERE MIN(b+(1-r)*d,h-r*d)>=0
), best AS (SELECT scenario,MAX(value) value FROM options GROUP BY scenario)
SELECT b.scenario,b.value upper_limit_usd_million,MAX(o.attained) attainable
 FROM best b JOIN options o ON b.scenario=o.scenario AND ABS(b.value-o.value)<1e-9
 GROUP BY b.scenario,b.value
