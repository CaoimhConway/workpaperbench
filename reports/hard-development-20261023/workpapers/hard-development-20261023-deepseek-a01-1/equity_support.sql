WITH p AS (
 SELECT commitment, utilised_including_lc, covenant_availability, test_threshold,
        commitment - utilised_including_lc AS max_borrow,
        covenant_availability - test_threshold AS trigger_borrow
 FROM facility
),
c AS (
 SELECT scenario,
        ebitda - net_cash_capex AS numerator,
        scheduled_principal + existing_cash_interest + cash_tax + ordinary_dividend AS fixed_base,
        ebitda - net_cash_capex - scheduled_principal - existing_cash_interest - cash_tax - ordinary_dividend - working_capital_outflow AS pre_div_cash,
        new_debt_cash_rate AS r
 FROM planning_cases
),
x AS (
 SELECT c.*, p.max_borrow, p.trigger_borrow,
        (c.numerator - c.fixed_base - et.special_dividend) / c.r AS ratio_borrow,
        et.target, et.special_dividend AS dividend
 FROM c CROSS JOIN p CROSS JOIN equity_targets et
),
y AS (
 SELECT *,
        MIN(max_borrow, trigger_borrow) AS untested_borrow,
        CASE WHEN trigger_borrow <= max_borrow AND ratio_borrow >= trigger_borrow
             THEN 1 ELSE 0 END AS tested_valid,
        CASE WHEN trigger_borrow <= max_borrow AND ratio_borrow >= trigger_borrow
             THEN MIN(max_borrow, ratio_borrow) END AS tested_borrow
 FROM x
),
z AS (
 SELECT *,
        MAX(0.0, dividend - pre_div_cash - (1.0-r) * untested_borrow) AS untested_e,
        CASE WHEN tested_valid = 1
             THEN MAX(0.0, dividend - pre_div_cash - (1.0-r) * tested_borrow) END AS tested_e
 FROM y
)
SELECT scenario, target,
       CASE WHEN tested_e IS NOT NULL AND tested_e <= untested_e + 1e-9
            THEN tested_e ELSE untested_e END AS lower_limit_usd_million,
       CASE WHEN tested_e IS NOT NULL AND tested_e <= untested_e + 1e-9 THEN 1
            WHEN max_borrow < trigger_borrow THEN 1
            WHEN untested_e <= 0.0 THEN 1
            ELSE 0 END AS attainable
FROM z;
