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
calc AS (
 SELECT c.*, p.max_borrow, p.trigger_borrow,
        c.numerator - c.fixed_base - c.pre_div_cash AS b_intersection,
        MIN(p.max_borrow, p.trigger_borrow) AS b_untested_cap,
        p.trigger_borrow <= p.max_borrow AS tested_region_exists
 FROM c CROSS JOIN p
),
tested AS (
 SELECT *,
        MIN(max_borrow, MAX(trigger_borrow, b_intersection)) AS b_tested_peak
 FROM calc
),
cand AS (
 SELECT *,
        pre_div_cash + (1.0-r) * b_untested_cap AS untested_candidate,
        MIN(pre_div_cash + (1.0-r) * b_tested_peak,
            numerator - fixed_base - r * b_tested_peak) AS tested_candidate
 FROM tested
)
SELECT scenario,
       CASE WHEN tested_region_exists
            THEN MAX(untested_candidate, tested_candidate)
            ELSE untested_candidate END AS upper_limit_usd_million,
       CASE WHEN tested_region_exists = 0 THEN 1
            WHEN tested_candidate >= untested_candidate - 1e-9 THEN 1
            ELSE 0 END AS attainable
FROM cand;
