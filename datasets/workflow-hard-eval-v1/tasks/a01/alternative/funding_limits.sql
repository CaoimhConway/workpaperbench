WITH RECURSIVE inputs AS (
 SELECT c.*,f.*,period,seasonal,
 CASE WHEN seasonal=1 THEN seasonal_inventory_rate ELSE ordinary_inventory_rate END rate,
 loans+letters_of_credit exposure FROM collateral_cases c CROSS JOIN facility_terms f CROSS JOIN period_cases
), raw AS (
 SELECT *,receivable_rate*(credit_card_receivables+pharmacy_receivables)+rate*regular_inventory_cost*regular_appraisal u,
 rate*perishable_inventory_cost*perishable_appraisal p,script_rate*script_liquidation_value s,
 availability_reserves r,rate*regular_appraisal*regular_purchase_fraction du,
 rate*perishable_appraisal*(1-regular_purchase_fraction) dp,
 shared_fraction/(1-shared_fraction) q,perishable_fraction/(1-perishable_fraction) k FROM inputs
) , search(scenario,period,step,lo,hi) AS (
 SELECT scenario,period,0,0.0,commitment-exposure FROM raw UNION ALL
 SELECT z.scenario,z.period,step+1,
 CASE WHEN MIN(commitment,u+du*((lo+hi)/2)+MIN(s,shared_dollar_cap,q*(u+p+(du+dp)*((lo+hi)/2)-r))+MIN(p+dp*((lo+hi)/2),k*(u+du*((lo+hi)/2)+s-r))-r)>=exposure+(lo+hi)/2 THEN (lo+hi)/2 ELSE lo END,
 CASE WHEN MIN(commitment,u+du*((lo+hi)/2)+MIN(s,shared_dollar_cap,q*(u+p+(du+dp)*((lo+hi)/2)-r))+MIN(p+dp*((lo+hi)/2),k*(u+du*((lo+hi)/2)+s-r))-r)>=exposure+(lo+hi)/2 THEN hi ELSE (lo+hi)/2 END
 FROM search z JOIN raw USING(scenario,period) WHERE step<60
), valued AS (SELECT raw.*,lo purchase_cost,u+du*lo+MIN(s,shared_dollar_cap,q*(u+p+(du+dp)*lo-r))+MIN(p+dp*lo,k*(u+du*lo+s-r))-r b FROM search JOIN raw USING(scenario,period) WHERE step=60)
SELECT scenario,period,purchase_cost maximum_purchase_usd_million,b borrowing_base_usd_million,
 MIN(commitment,b)-exposure-purchase_cost funding_surplus_usd_million FROM valued
