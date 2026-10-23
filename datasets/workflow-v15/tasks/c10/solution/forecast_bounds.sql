SELECT CAST(f.year AS INTEGER) year,f.bound,f.revenue_usd_million,
100.0*(1000.0*f.revenue_usd_million/a.revenue_usd_thousand-1) implied_reported_revenue_growth_pct,
f.revenue_usd_million*f.target_operating_margin_pct/100.0 implied_operating_income_usd_million,
100.0*(10.0*f.revenue_usd_million*f.target_operating_margin_pct/a.operating_income_usd_thousand-1) implied_operating_growth_pct,
f.included_acquisition_expense_usd_million FROM forecasts f CROSS JOIN annual_margin a WHERE f.year=2026 AND a.year=2025
