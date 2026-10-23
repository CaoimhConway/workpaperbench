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
) , valued AS (SELECT *,u+du*purchase_cost+MIN(s,shared_dollar_cap,q*(u+p+(du+dp)*purchase_cost-r))+MIN(p+dp*purchase_cost,k*(u+du*purchase_cost+s-r))-r b FROM raw CROSS JOIN purchase_sizes) SELECT scenario,period,proposal,b borrowing_base_usd_million,exposure+purchase_cost revolving_exposure_usd_million,MIN(commitment,b)-exposure-purchase_cost funding_surplus_usd_million,CASE WHEN MIN(commitment,b)>=exposure+purchase_cost THEN 1 ELSE 0 END feasible FROM valued
