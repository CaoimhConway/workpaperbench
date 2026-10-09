SELECT 'FY2026' fiscal_year,p.amount_usd_billion observed_exit_arr_usd_billion,
c.amount_usd_billion revalued_opening_arr_usd_billion,
1000.0*(c.amount_usd_billion-p.amount_usd_billion) revaluation_usd_million,
t.value target_arr_growth_pct,p.amount_usd_billion*(1+t.value/100.0) implied_target_arr_usd_billion
FROM arr_basis p CROSS JOIN arr_basis c JOIN targets t ON t.period='FY2026' AND t.measure='ending_arr_growth_pct'
WHERE p.basis='FY2025_exit' AND c.basis='FY2026_opening_revalued'
