WITH f AS (
 SELECT commitment, utilised_including_lc, covenant_availability, test_threshold
 FROM facility
),
p AS (
 SELECT scenario,
        ebitda - net_cash_capex AS numerator,
        scheduled_principal + existing_cash_interest + cash_tax + ordinary_dividend AS fixed_base,
        ebitda - net_cash_capex - scheduled_principal - existing_cash_interest - cash_tax - ordinary_dividend - working_capital_outflow AS pre_dividend_cash,
        new_debt_cash_rate AS r
 FROM planning_cases
),
x AS (
 SELECT p.scenario, pr.proposal, pr.special_dividend AS dividend,
        p.numerator, p.fixed_base, p.r,
        MAX(0.0, (pr.special_dividend - p.pre_dividend_cash) / (1.0 - p.r)) AS required_draw
 FROM p CROSS JOIN proposals pr
)
SELECT scenario, proposal, required_draw AS required_draw_usd_million,
       f.covenant_availability - x.required_draw AS covenant_availability_usd_million,
       x.numerator / (x.fixed_base + x.r * x.required_draw + x.dividend) AS fixed_charge_ratio,
       CASE WHEN f.covenant_availability - x.required_draw <= f.test_threshold THEN 1 ELSE 0 END AS covenant_tested,
       CASE WHEN x.required_draw <= f.commitment - f.utilised_including_lc
             AND (f.covenant_availability - x.required_draw > f.test_threshold
                  OR x.numerator / (x.fixed_base + x.r * x.required_draw + x.dividend) >= 1.0)
            THEN 1 ELSE 0 END AS feasible
FROM x CROSS JOIN f;
