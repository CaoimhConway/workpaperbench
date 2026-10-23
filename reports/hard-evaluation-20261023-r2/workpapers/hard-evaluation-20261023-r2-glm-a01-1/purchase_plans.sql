WITH terms AS (
  SELECT * FROM facility_terms
),
base AS (
  SELECT
    c.scenario,
    p.period,
    t.commitment,
    t.receivable_rate * (c.credit_card_receivables + c.pharmacy_receivables) AS receivable_advance,
    t.script_rate * c.script_liquidation_value AS script_advance,
    CASE WHEN p.seasonal = 1 THEN t.seasonal_inventory_rate ELSE t.ordinary_inventory_rate END
      * c.regular_appraisal * c.regular_inventory_cost AS regular_advance,
    CASE WHEN p.seasonal = 1 THEN t.seasonal_inventory_rate ELSE t.ordinary_inventory_rate END
      * c.regular_appraisal * c.regular_purchase_fraction AS regular_slope,
    CASE WHEN p.seasonal = 1 THEN t.seasonal_inventory_rate ELSE t.ordinary_inventory_rate END
      * c.perishable_appraisal * c.perishable_inventory_cost AS perishable_advance,
    CASE WHEN p.seasonal = 1 THEN t.seasonal_inventory_rate ELSE t.ordinary_inventory_rate END
      * c.perishable_appraisal * (1.0 - c.regular_purchase_fraction) AS perishable_slope,
    c.availability_reserves AS reserve,
    c.loans + c.letters_of_credit AS existing_exposure,
    t.shared_dollar_cap,
    t.shared_fraction / (1.0 - t.shared_fraction) AS shared_multiplier,
    t.perishable_fraction / (1.0 - t.perishable_fraction) AS perishable_multiplier
  FROM collateral_cases AS c
  CROSS JOIN period_cases AS p
  CROSS JOIN terms AS t
),
post_purchase AS (
  SELECT
    b.*,
    z.proposal,
    z.purchase_cost,
    b.regular_advance + b.regular_slope * z.purchase_cost AS post_regular_advance,
    b.perishable_advance + b.perishable_slope * z.purchase_cost AS post_perishable_advance
  FROM base AS b
  CROSS JOIN purchase_sizes AS z
),
capped AS (
  SELECT
    *,
    MIN(script_advance, MIN(shared_dollar_cap, shared_multiplier * (
      receivable_advance + post_regular_advance + post_perishable_advance - reserve
    ))) AS shared_advance,
    MIN(post_perishable_advance, perishable_multiplier * (
      receivable_advance + script_advance + post_regular_advance - reserve
    )) AS capped_perishable_advance
  FROM post_purchase
),
funded AS (
  SELECT
    *,
    receivable_advance + shared_advance + post_regular_advance
      + capped_perishable_advance - reserve AS borrowing_base,
    existing_exposure + purchase_cost AS revolving_exposure,
    MIN(commitment, receivable_advance + shared_advance + post_regular_advance
      + capped_perishable_advance - reserve) - existing_exposure - purchase_cost
      AS funding_surplus
  FROM capped
)
SELECT
  scenario,
  period,
  proposal,
  borrowing_base AS borrowing_base_usd_million,
  revolving_exposure AS revolving_exposure_usd_million,
  funding_surplus AS funding_surplus_usd_million,
  CASE WHEN funding_surplus >= 0.0 THEN 1 ELSE 0 END AS feasible
FROM funded
ORDER BY scenario, period, proposal;
