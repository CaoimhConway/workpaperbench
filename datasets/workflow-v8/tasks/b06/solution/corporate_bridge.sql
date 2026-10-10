WITH s AS (SELECT year,SUM(bookings_usd_million) b,SUM(revenue_usd_million) r,SUM(adjusted_ebitda_usd_million) e FROM segments GROUP BY year)
SELECT CAST(p.year AS INTEGER) year,e segment_sum_usd_million,p.corporate_cost_usd_million,e+p.corporate_cost_usd_million total_adjusted_ebitda_usd_million,
e+p.corporate_cost_usd_million-p.adjusted_ebitda_usd_million ebitda_residual_usd_million,
b-p.bookings_usd_million bookings_residual_usd_million,r-p.revenue_usd_million revenue_residual_usd_million,
100.0*(e+p.corporate_cost_usd_million)/b total_ebitda_to_bookings_pct FROM platform p JOIN s ON p.year=s.year WHERE p.year IN (2024,2025)
