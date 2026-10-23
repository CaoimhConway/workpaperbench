WITH terms AS (
  SELECT
    p.scenario,
    pr.proposal,
    pr.special_dividend,
    p.new_debt_cash_rate,
    p.ebitda - p.net_cash_capex AS covenant_numerator,
    p.scheduled_principal + p.existing_cash_interest + p.cash_tax
      + p.ordinary_dividend AS existing_fixed_charges,
    p.net_cash_capex + p.scheduled_principal + p.existing_cash_interest
      + p.cash_tax + p.ordinary_dividend + p.working_capital_outflow
      - p.ebitda AS pre_special_cash_deficit,
    f.covenant_availability,
    f.test_threshold,
    f.commitment - f.utilised_including_lc AS facility_capacity
  FROM planning_cases AS p
  CROSS JOIN proposals AS pr
  CROSS JOIN facility AS f
), sized AS (
  SELECT
    terms.*,
    MAX(
      (pre_special_cash_deficit + special_dividend)
        / (1.0 - new_debt_cash_rate),
      0.0
    ) AS required_draw_usd_million
  FROM terms
), scored AS (
  SELECT
    sized.*,
    covenant_availability - required_draw_usd_million
      AS covenant_availability_usd_million,
    covenant_numerator / NULLIF(
      existing_fixed_charges + special_dividend
        + new_debt_cash_rate * required_draw_usd_million,
      0.0
    ) AS fixed_charge_ratio
  FROM sized
)
SELECT
  scenario,
  proposal,
  required_draw_usd_million,
  covenant_availability_usd_million,
  fixed_charge_ratio,
  CAST(covenant_availability_usd_million <= test_threshold AS INTEGER)
    AS covenant_tested,
  CAST(
    required_draw_usd_million <= facility_capacity
    AND (
      covenant_availability_usd_million > test_threshold
      OR fixed_charge_ratio >= 1.0
    )
  AS INTEGER) AS feasible
FROM scored;
