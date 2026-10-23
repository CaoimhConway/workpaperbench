WITH inputs AS (
 SELECT c.*,f.*,period,seasonal,
 CASE WHEN seasonal=1 THEN seasonal_inventory_rate ELSE ordinary_inventory_rate END rate,
 loans+letters_of_credit exposure FROM collateral_cases c CROSS JOIN facility_terms f CROSS JOIN period_cases
), raw AS (
 SELECT *,receivable_rate*(credit_card_receivables+pharmacy_receivables)+rate*regular_inventory_cost*regular_appraisal u,
 rate*perishable_inventory_cost*perishable_appraisal p,script_rate*script_liquidation_value s,
 availability_reserves r,rate*regular_appraisal*regular_purchase_fraction du,
 rate*perishable_appraisal*(1-regular_purchase_fraction) dp,
 shared_fraction/(1-shared_fraction) q,perishable_fraction/(1-perishable_fraction) k FROM inputs
) , script_branches AS (
 SELECT scenario,period,s intercept,0.0 slope FROM raw UNION ALL
 SELECT scenario,period,shared_dollar_cap,0.0 FROM raw UNION ALL
 SELECT scenario,period,q*(u+p-r),q*(du+dp) FROM raw
), perishable_branches AS (
 SELECT scenario,period,p intercept,dp slope FROM raw UNION ALL
 SELECT scenario,period,k*(u+s-r),k*du FROM raw
), bounds AS (
 SELECT scenario,period,commitment-exposure bound FROM raw UNION ALL
 SELECT a.scenario,a.period,(u+s.intercept+p.intercept-r-exposure)/(1-du-s.slope-p.slope)
 FROM raw a JOIN script_branches s USING(scenario,period) JOIN perishable_branches p USING(scenario,period)
 WHERE du+s.slope+p.slope<1
), limits AS (SELECT scenario,period,MIN(bound) purchase_cost FROM bounds GROUP BY scenario,period), valued AS (
 SELECT a.*,purchase_cost,u+du*purchase_cost+MIN(s,shared_dollar_cap,q*(u+p+(du+dp)*purchase_cost-r))+MIN(p+dp*purchase_cost,k*(u+du*purchase_cost+s-r))-r b FROM raw a JOIN limits USING(scenario,period)
)
SELECT scenario,period,purchase_cost maximum_purchase_usd_million,b borrowing_base_usd_million,
 MIN(commitment,b)-exposure-purchase_cost funding_surplus_usd_million FROM valued
