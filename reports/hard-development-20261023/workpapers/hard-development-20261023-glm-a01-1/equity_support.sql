WITH terms AS (
  SELECT
    p.scenario,
    e.target,
    e.special_dividend,
    p.new_debt_cash_rate,
    p.ebitda - p.net_cash_capex AS covenant_numerator,
    p.scheduled_principal + p.existing_cash_interest + p.cash_tax
      + p.ordinary_dividend AS existing_fixed_charges,
    p.net_cash_capex + p.scheduled_principal + p.existing_cash_interest
      + p.cash_tax + p.ordinary_dividend + p.working_capital_outflow
      - p.ebitda AS pre_special_cash_deficit,
    f.covenant_availability,
    f.test_threshold,
    MAX(f.commitment - f.utilised_including_lc, 0.0) AS facility_capacity
  FROM planning_cases AS p
  CROSS JOIN equity_targets AS e
  CROSS JOIN facility AS f
), bounded AS (
  SELECT
    terms.*,
    pre_special_cash_deficit + special_dividend AS cash_need,
    covenant_availability - test_threshold AS trigger_draw,
    CASE
      WHEN new_debt_cash_rate = 0.0 THEN -1.0
      ELSE (covenant_numerator - existing_fixed_charges
        - special_dividend) / new_debt_cash_rate
    END AS ratio_draw_boundary
  FROM terms
), candidates AS (
  SELECT
    bounded.*,
    CASE WHEN trigger_draw > 0.0 THEN
      MIN(trigger_draw, facility_capacity)
    ELSE -1.0
    END AS exemption_supremum,
    CASE
      WHEN new_debt_cash_rate = 0.0 THEN
        CASE WHEN existing_fixed_charges + special_dividend > 0.0
          AND covenant_numerator >= existing_fixed_charges + special_dividend
        THEN facility_capacity ELSE -1.0 END
      WHEN ratio_draw_boundary >= 0.0 THEN
        MIN(facility_capacity, ratio_draw_boundary)
      ELSE -1.0
    END AS ratio_supremum
  FROM bounded
), limited AS (
  SELECT
    candidates.*,
    MAX(exemption_supremum, ratio_supremum, 0.0) AS max_feasible_draw
  FROM candidates
), supported AS (
  SELECT
    limited.*,
    MAX(
      cash_need - (1.0 - new_debt_cash_rate) * max_feasible_draw,
      0.0
    ) AS lower_limit_usd_million
  FROM limited
), checked AS (
  SELECT
    supported.*,
    MAX(
      (cash_need - lower_limit_usd_million)
        / (1.0 - new_debt_cash_rate),
      0.0
    ) AS draw_at_lower_limit,
    CASE
      WHEN existing_fixed_charges + special_dividend
        + new_debt_cash_rate * MAX(
          (cash_need - lower_limit_usd_million)
            / (1.0 - new_debt_cash_rate),
          0.0
        ) > 0.0
      THEN covenant_numerator >= existing_fixed_charges
        + special_dividend + new_debt_cash_rate * MAX(
          (cash_need - lower_limit_usd_million)
            / (1.0 - new_debt_cash_rate),
          0.0
        )
      ELSE 0
    END AS ratio_compliant_at_limit
  FROM supported
)
SELECT
  scenario,
  target,
  lower_limit_usd_million,
  CAST(
    draw_at_lower_limit <= facility_capacity
    AND (
      draw_at_lower_limit < trigger_draw
      OR ratio_compliant_at_limit
    )
  AS INTEGER) AS attainable
FROM checked;
