WITH terms AS (
  SELECT * FROM facility_terms
),
cases AS (
  SELECT
    c.scenario,
    p.period,
    t.commitment,
    t.receivable_rate * (c.credit_card_receivables + c.pharmacy_receivables) AS receivable_advance,
    t.script_rate * c.script_liquidation_value AS script_advance,
    CASE WHEN p.seasonal = 1 THEN t.seasonal_inventory_rate ELSE t.ordinary_inventory_rate END
      * c.regular_appraisal * c.regular_inventory_cost AS regular_advance,
    CASE WHEN p.seasonal = 1 THEN t.seasonal_inventory_rate ELSE t.ordinary_inventory_rate END
      * c.perishable_appraisal * c.perishable_inventory_cost AS perishable_advance,
    c.availability_reserves AS reserve,
    c.loans,
    c.letters_of_credit,
    t.shared_dollar_cap,
    t.shared_fraction / (1.0 - t.shared_fraction) AS shared_multiplier,
    t.perishable_fraction / (1.0 - t.perishable_fraction) AS perishable_multiplier
  FROM collateral_cases AS c
  CROSS JOIN period_cases AS p
  CROSS JOIN terms AS t
),
capped AS (
  SELECT
    *,
    MIN(script_advance, MIN(shared_dollar_cap, shared_multiplier * (
      receivable_advance + regular_advance + perishable_advance - reserve
    ))) AS shared_advance,
    MIN(perishable_advance, perishable_multiplier * (
      receivable_advance + script_advance + regular_advance - reserve
    )) AS capped_perishable_advance
  FROM cases
)
SELECT
  scenario,
  period,
  receivable_advance + script_advance + regular_advance + perishable_advance - reserve
    AS uncapped_advance_usd_million,
  receivable_advance + shared_advance + regular_advance + capped_perishable_advance - reserve
    AS borrowing_base_usd_million,
  MAX(0.0, MIN(commitment, receivable_advance + shared_advance + regular_advance
    + capped_perishable_advance - reserve) - loans - letters_of_credit)
    AS available_draw_usd_million
FROM capped
ORDER BY scenario, period;
