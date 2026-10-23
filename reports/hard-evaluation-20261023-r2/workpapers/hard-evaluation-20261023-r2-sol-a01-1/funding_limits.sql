-- All amounts are USD million. All comparisons use unrounded values.
-- There is no eligible pharmacy inventory in these authored cases.
-- A borrowing base without a named cap retains the other definitions.
-- With A = receivable advances + regular advance - reserves, S = raw scripts,
-- P = raw perishables, f = shared fraction, g = perishable fraction:
-- allowed scripts = min(S, shared dollar cap, f/(1-f)*(A+P));
-- allowed perishables = min(P, g/(1-g)*(A+S)).
-- The factors solve each retained cap's self-reference algebraically.
-- Each capped term is the minimum of affine functions of purchase cost x.
-- Their sum is the minimum of all six affine sums. Funding requires
-- exposure + x <= every such sum, and exposure + x <= commitment.
-- Intersect these linear constraints; the smallest upper bound is sharp.
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
coefficients AS (
    SELECT *,
           (credit_card_receivables + pharmacy_receivables) * receivable_rate
             + regular_inventory_cost * regular_appraisal * inventory_rate
             - availability_reserves AS a0,
           regular_purchase_fraction * regular_appraisal * inventory_rate AS a1,
           script_liquidation_value * script_rate AS s0,
           perishable_inventory_cost * perishable_appraisal * inventory_rate AS p0,
           (1.0 - regular_purchase_fraction) * perishable_appraisal * inventory_rate AS p1,
           loans + letters_of_credit AS opening_exposure
    FROM inputs
),
script_lines AS (
    SELECT scenario, period, s0 AS intercept, 0.0 AS slope FROM coefficients
    UNION ALL
    SELECT scenario, period, shared_dollar_cap, 0.0 FROM coefficients
    UNION ALL
    SELECT scenario, period, shared_multiplier * (a0 + p0),
           shared_multiplier * (a1 + p1) FROM coefficients
),
perishable_lines AS (
    SELECT scenario, period, p0 AS intercept, p1 AS slope FROM coefficients
    UNION ALL
    SELECT scenario, period, perishable_multiplier * (a0 + s0),
           perishable_multiplier * a1 FROM coefficients
),
constraints AS (
    SELECT c.scenario, c.period,
           c.a0 + s.intercept + p.intercept - c.opening_exposure AS headroom,
           1.0 - c.a1 - s.slope - p.slope AS cost_coefficient
    FROM coefficients AS c
    JOIN script_lines AS s USING (scenario, period)
    JOIN perishable_lines AS p USING (scenario, period)
    UNION ALL
    SELECT scenario, period, commitment - opening_exposure, 1.0 FROM coefficients
),
intervals AS (
    SELECT scenario, period,
           MIN(CASE WHEN cost_coefficient > 0.0
                    THEN headroom / cost_coefficient END) AS upper_bound,
           MAX(CASE WHEN cost_coefficient < 0.0
                    THEN headroom / cost_coefficient ELSE 0.0 END) AS lower_bound,
           MIN(CASE WHEN cost_coefficient = 0.0 AND headroom < 0.0
                    THEN 0 ELSE 1 END) AS consistent
    FROM constraints GROUP BY scenario, period
),
purchases AS (
    SELECT i.*,
           CASE WHEN b.consistent = 1 AND b.upper_bound >= b.lower_bound
                THEN b.upper_bound END AS purchase_cost
    FROM inputs AS i JOIN intervals AS b USING (scenario, period)
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
SELECT scenario, period, purchase_cost AS maximum_purchase_usd_million,
       borrowing_base AS borrowing_base_usd_million,
       MIN(commitment, borrowing_base) - loans - letters_of_credit - purchase_cost
         AS funding_surplus_usd_million
FROM valued;
