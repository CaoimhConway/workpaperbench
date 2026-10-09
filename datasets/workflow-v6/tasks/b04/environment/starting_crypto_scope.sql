SELECT s.period,s.scope,CAST(s.months AS INTEGER) months,s.volume_usd_billion,
100.0*s.volume_usd_billion/t.volume_usd_billion share_of_combined_pct,
1.0*s.volume_usd_billion/s.months monthly_average_usd_billion FROM crypto_volumes s JOIN crypto_volumes t ON t.period=s.period AND t.scope='total'
WHERE s.period IN ('Q4FY2025','January2026') AND s.scope IN ('app','bitstamp')
