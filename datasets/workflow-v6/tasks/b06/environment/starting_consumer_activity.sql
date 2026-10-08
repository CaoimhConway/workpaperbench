SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,trips_million,mapcs_million,
1.0*trips_million/mapcs_million quarterly_trips_per_monthly_consumer,
1.0*trips_million/mapcs_million monthly_trips_per_monthly_consumer FROM platform WHERE year IN (2024,2025)
