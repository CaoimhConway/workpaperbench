-- B is additional cash borrowing; new interest must itself be funded.
WITH inputs AS (
    SELECT p.*, d.proposal, d.special_dividend,
           f.commitment - f.utilised_including_lc AS draw_capacity,
           f.covenant_availability AS opening_availability,
           f.test_threshold,
           p.ebitda - p.net_cash_capex AS numerator,
           p.scheduled_principal + p.existing_cash_interest
             + p.cash_tax + p.ordinary_dividend AS fixed_charges
    FROM planning_cases p CROSS JOIN proposals d CROSS JOIN facility f
), funding AS (
    SELECT *, fixed_charges + net_cash_capex + working_capital_outflow
                   + special_dividend - ebitda AS cash_deficit
    FROM inputs
), draws AS (
    SELECT *, CASE WHEN cash_deficit <= 0 THEN 0.0
                   WHEN new_debt_cash_rate < 1
                     THEN cash_deficit / (1.0 - new_debt_cash_rate)
                   ELSE NULL END AS draw
    FROM funding
), tests AS (
    SELECT *, opening_availability - draw AS availability,
           1.0 * numerator / (fixed_charges + special_dividend
                                    + new_debt_cash_rate * draw) AS ratio
    FROM draws
)
SELECT scenario, proposal,
       draw AS required_draw_usd_million,
       availability AS covenant_availability_usd_million,
       ratio AS fixed_charge_ratio,
       CASE WHEN availability <= test_threshold THEN 1 ELSE 0 END AS covenant_tested,
       CASE WHEN draw >= 0 AND draw <= draw_capacity
                  AND (cash_deficit <= 0 OR new_debt_cash_rate < 1)
                  AND (availability > test_threshold OR ratio >= 1.0)
            THEN 1 ELSE 0 END AS feasible
FROM tests;
