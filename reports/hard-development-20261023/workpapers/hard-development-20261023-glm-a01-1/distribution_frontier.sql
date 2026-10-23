WITH terms AS (
  SELECT
    p.scenario,
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
  CROSS JOIN facility AS f
), bounds AS (
  SELECT
    terms.*,
    covenant_availability - test_threshold AS strict_trigger_draw,
    pre_special_cash_deficit + covenant_numerator
      - existing_fixed_charges AS ratio_draw_boundary
  FROM terms
), selected AS (
  SELECT
    bounds.*,
    CASE
      WHEN strict_trigger_draw > 0.0
        AND facility_capacity < strict_trigger_draw THEN
        (1.0 - new_debt_cash_rate) * facility_capacity
          - pre_special_cash_deficit
      WHEN strict_trigger_draw > 0.0
        AND ratio_draw_boundary >= strict_trigger_draw THEN
        (1.0 - new_debt_cash_rate)
          * MIN(facility_capacity, ratio_draw_boundary)
          - pre_special_cash_deficit
      WHEN strict_trigger_draw > 0.0 THEN
        (1.0 - new_debt_cash_rate) * strict_trigger_draw
          - pre_special_cash_deficit
      WHEN ratio_draw_boundary >= 0.0 THEN
        (1.0 - new_debt_cash_rate)
          * MIN(facility_capacity, ratio_draw_boundary)
          - pre_special_cash_deficit
      ELSE covenant_numerator - existing_fixed_charges
    END AS raw_upper_limit
)
SELECT
  scenario,
  MAX(raw_upper_limit, 0.0) AS upper_limit_usd_million,
  CASE
    WHEN raw_upper_limit >= 0.0
      AND NOT (
        strict_trigger_draw > 0.0
        AND facility_capacity >= strict_trigger_draw
        AND ratio_draw_boundary < strict_trigger_draw
      ) THEN 1
    WHEN raw_upper_limit >= 0.0 THEN 0
    WHEN strict_trigger_draw <= 0.0
      AND ratio_draw_boundary < 0.0
      AND covenant_numerator >= existing_fixed_charges THEN 1
    ELSE 0
  END AS attainable
FROM bounds;
