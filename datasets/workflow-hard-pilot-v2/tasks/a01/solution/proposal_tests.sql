WITH p AS (
 SELECT s.*,f.commitment-f.utilised_including_lc capacity,
 f.covenant_availability-f.test_threshold trigger_draw,f.covenant_availability,
 scheduled_principal+existing_cash_interest+cash_tax+ordinary_dividend fixed_charges
 FROM planning_cases s CROSS JOIN facility f
), q AS (
 SELECT *,ebitda-net_cash_capex-fixed_charges h,
 ebitda-net_cash_capex-fixed_charges-working_capital_outflow b,
 new_debt_cash_rate r FROM p
) , proposed AS (
 SELECT q.*,v.*,MAX(0.0,(special_dividend-b)/(1-r)) draw FROM q CROSS JOIN proposals v
), tested AS (
 SELECT *, (ebitda-net_cash_capex)/(fixed_charges+r*draw+special_dividend) ratio FROM proposed
)
SELECT scenario,proposal,draw required_draw_usd_million,
 covenant_availability-draw covenant_availability_usd_million,ratio fixed_charge_ratio,
 CASE WHEN draw>=trigger_draw THEN 1 ELSE 0 END covenant_tested,
 CASE WHEN draw<=capacity AND (draw<trigger_draw OR ratio>=1) THEN 1 ELSE 0 END feasible FROM tested
