SELECT CASE WHEN c.period='FY2025' THEN 'FY' ELSE 'Q4FY' END window,c.region,
p.purchase_usd_billion prior_purchase_usd_billion,c.purchase_usd_billion current_purchase_usd_billion,
c.purchase_usd_billion-p.purchase_usd_billion change_usd_billion,
100.0*(c.purchase_usd_billion-p.purchase_usd_billion)/(wc.purchase_usd_billion-wp.purchase_usd_billion) contribution_to_worldwide_purchase_growth_pct,
1000.0*p.purchase_usd_billion/p.purchase_transactions_million prior_average_purchase_usd,
1000.0*c.purchase_usd_billion/c.purchase_transactions_million current_average_purchase_usd,
100.0*((c.purchase_usd_billion/c.purchase_transactions_million)/(p.purchase_usd_billion/p.purchase_transactions_million)-1) average_purchase_growth_pct,
c.purchase_usd_billion+c.cash_usd_billion-c.gdv_usd_billion current_gdv_residual_usd_billion
FROM regions c JOIN regions p ON c.region=p.region AND ((c.period='FY2025' AND p.period='FY2024') OR (c.period='Q4FY2025' AND p.period='Q4FY2024'))
JOIN worldwide wc ON wc.period=c.period JOIN worldwide wp ON wp.period=p.period
