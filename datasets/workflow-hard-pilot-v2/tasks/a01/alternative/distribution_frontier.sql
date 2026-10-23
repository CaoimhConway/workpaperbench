WITH p AS (
 SELECT s.*,f.commitment-f.utilised_including_lc capacity,
 f.covenant_availability-f.test_threshold trigger_draw,f.covenant_availability,
 scheduled_principal+existing_cash_interest+cash_tax+ordinary_dividend fixed_charges
 FROM planning_cases s CROSS JOIN facility f
), q AS (
 SELECT *,ebitda-net_cash_capex-fixed_charges h,
 ebitda-net_cash_capex-fixed_charges-working_capital_outflow b,
 new_debt_cash_rate r FROM p
) , envelope AS (
 SELECT *,b+(1-r)*MIN(capacity,trigger_draw) inactive_limit,
 CASE WHEN capacity>=trigger_draw THEN
 MIN(b+(1-r)*capacity,h-r*trigger_draw,(1-r)*h+r*b) ELSE -1 END active_limit FROM q
)
SELECT scenario,MAX(inactive_limit,active_limit) upper_limit_usd_million,
 CASE WHEN capacity<trigger_draw OR active_limit>=inactive_limit THEN 1 ELSE 0 END attainable FROM envelope
