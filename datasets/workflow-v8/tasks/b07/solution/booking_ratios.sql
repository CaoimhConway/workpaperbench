SELECT CAST(year AS INTEGER) year,CAST(quarter AS INTEGER) quarter,1000.0*gbv_usd_billion gbv_usd_million,nights_and_seats_million,
1000.0*gbv_usd_billion/nights_and_seats_million rounded_input_adr_usd,
1000.0*gbv_usd_billion/nights_and_seats_million-reported_adr_usd adr_rounding_residual_usd,
revenue_usd_million/(10.0*gbv_usd_billion) implied_revenue_to_gbv_pct FROM quarters WHERE year IN (2024,2025)
