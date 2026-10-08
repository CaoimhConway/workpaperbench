SELECT CAST(year AS INTEGER) year,segment,bookings_usd_million,revenue_usd_million,adjusted_ebitda_usd_million,
100.0*revenue_usd_million/bookings_usd_million revenue_to_bookings_pct,
100.0*adjusted_ebitda_usd_million/bookings_usd_million ebitda_to_bookings_pct FROM segments WHERE year IN (2024,2025)
