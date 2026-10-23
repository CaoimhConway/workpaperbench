-- All amounts are USD million. All comparisons use unrounded values.
-- There is no eligible pharmacy inventory in these authored cases.
-- A borrowing base without a named cap retains the other definitions.
-- With A = receivable advances + regular advance - reserves, S = raw scripts,
-- P = raw perishables, f = shared fraction, g = perishable fraction:
-- allowed scripts = min(S, shared dollar cap, f/(1-f)*(A+P));
-- allowed perishables = min(P, g/(1-g)*(A+S)).
-- The factors solve each retained cap's self-reference algebraically.
WITH
inputs AS (
    SELECT c.*, p.period, t.commitment, t.receivable_rate, t.script_rate,
           t.shared_dollar_cap,
           t.shared_fraction / (1.0 - t.shared_fraction) AS shared_multiplier,
           t.perishable_fraction / (1.0 - t.perishable_fraction) AS perishable_multiplier,
           CASE WHEN p.seasonal = 1 THEN t.seasonal_inventory_rate
                ELSE t.ordinary_inventory_rate END AS inventory_rate
    FROM collateral_cases AS c
    CROSS JOIN period_cases AS p
    CROSS JOIN facility_terms AS t
),
purchases AS (
    SELECT *, 0.0 AS purchase_cost FROM inputs
),
advances AS (
    SELECT *,
           (credit_card_receivables + pharmacy_receivables) * receivable_rate
             + (regular_inventory_cost + regular_purchase_fraction * purchase_cost)
               * regular_appraisal * inventory_rate
             - availability_reserves AS other_advance,
           script_liquidation_value * script_rate AS raw_scripts,
           (perishable_inventory_cost + (1.0 - regular_purchase_fraction) * purchase_cost)
             * perishable_appraisal * inventory_rate AS raw_perishables
    FROM purchases
),
valued AS (
    SELECT *,
           other_advance
             + MIN(raw_scripts, shared_dollar_cap,
                   shared_multiplier * (other_advance + raw_perishables))
             + MIN(raw_perishables,
                   perishable_multiplier * (other_advance + raw_scripts)) AS borrowing_base
    FROM advances
)
SELECT scenario, period,
       other_advance + raw_scripts + raw_perishables AS uncapped_advance_usd_million,
       borrowing_base AS borrowing_base_usd_million,
       MAX(0.0, MIN(commitment, borrowing_base) - loans - letters_of_credit)
         AS available_draw_usd_million
FROM valued;
