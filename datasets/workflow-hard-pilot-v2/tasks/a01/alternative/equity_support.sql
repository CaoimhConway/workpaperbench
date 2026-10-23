WITH p AS (
 SELECT s.*,f.commitment-f.utilised_including_lc capacity,
 f.covenant_availability-f.test_threshold trigger_draw,f.covenant_availability,
 scheduled_principal+existing_cash_interest+cash_tax+ordinary_dividend fixed_charges
 FROM planning_cases s CROSS JOIN facility f
), q AS (
 SELECT *,ebitda-net_cash_capex-fixed_charges h,
 ebitda-net_cash_capex-fixed_charges-working_capital_outflow b,
 new_debt_cash_rate r FROM p
) , limits AS (
 SELECT q.*,v.*,CASE WHEN capacity>=trigger_draw AND (h-special_dividend)/r>=trigger_draw
 THEN MIN(capacity,(h-special_dividend)/r) ELSE MIN(capacity,trigger_draw) END draw_limit,
 CASE WHEN capacity<trigger_draw OR (capacity>=trigger_draw AND (h-special_dividend)/r>=trigger_draw)
 THEN 1 ELSE 0 END closed FROM q CROSS JOIN equity_targets v
), gaps AS (SELECT *,special_dividend-b-(1-r)*draw_limit gap FROM limits)
SELECT scenario,target,MAX(0.0,gap) lower_limit_usd_million,
 CASE WHEN closed=1 OR gap<0 THEN 1 ELSE 0 END attainable FROM gaps
