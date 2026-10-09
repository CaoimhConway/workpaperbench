SELECT s.segment,r.amount_usd_million revenue_usd_million,s.volume_usd_billion spot_volume_usd_billion,
100.0*r.amount_usd_million/(1000*s.volume_usd_billion) apparent_revenue_to_spot_pct
FROM spot_volume s JOIN revenues r ON r.period=s.period AND r.measure=s.segment WHERE s.period='Q4FY2025'
