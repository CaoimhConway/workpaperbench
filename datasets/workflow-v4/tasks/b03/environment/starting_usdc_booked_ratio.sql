SELECT scope,average_usdc_usd_billion,revenue_usd_million,
100.0*revenue_usd_million/(1000*average_usdc_usd_billion) quarter_booked_ratio_pct,
100.0*revenue_usd_million/(1000*average_usdc_usd_billion) annualized_booked_ratio_pct FROM usdc_economics WHERE period='Q4FY2025'
