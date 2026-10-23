SELECT a.business, a.constant_currency_percent actual_cc_pct,g.low guidance_low_pct,
g.high guidance_high_pct,a.constant_currency_percent-(g.low+g.high)/2.0 midpoint_gap_pp
FROM growth a JOIN guidance g ON a.business=g.business WHERE g.issue_date='2024-10-30'
AND g.fiscal_period='Q2FY2025' AND g.basis='constant_currency'
