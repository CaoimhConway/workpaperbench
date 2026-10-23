WITH lines AS (SELECT MAX(CASE WHEN business_line='products' THEN net_sales END) p,
 MAX(CASE WHEN business_line='services' THEN net_sales END) s,
 MAX(CASE WHEN business_line='products' THEN (net_sales-cost_of_sales)/net_sales END) pm,
 MAX(CASE WHEN business_line='services' THEN (net_sales-cost_of_sales)/net_sales END) sm FROM business_lines),
 r AS (SELECT g.*,s.products_loss_pct/100.0 pr,s.services_loss_pct/100.0 sr,
 ROW_NUMBER() OVER(ORDER BY g.geography) rn FROM geographies g JOIN stress_rates s USING(geography)) SELECT geography,MAX(0,net_sales-s) lower_usd_million,
 MIN(net_sales,p) upper_usd_million FROM r CROSS JOIN lines
