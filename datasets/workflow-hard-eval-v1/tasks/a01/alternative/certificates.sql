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
) , counterfactuals AS (
 SELECT *,MIN(u+p+s-r,u+p+shared_dollar_cap-r,(u+p-r)/(1-shared_fraction)) without_perishables,
 MIN(u+s+p-r,(u+s-r)/(1-perishable_fraction)) without_shared FROM raw
), valued AS (
 SELECT *,u+MIN(s,shared_dollar_cap,shared_fraction*without_perishables)+MIN(p,perishable_fraction*without_shared)-r b FROM counterfactuals
)
SELECT scenario,period,u+p+s-r uncapped_advance_usd_million,b borrowing_base_usd_million,
 MIN(commitment,b)-exposure available_draw_usd_million FROM valued
