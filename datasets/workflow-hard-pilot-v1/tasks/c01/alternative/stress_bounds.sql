WITH lines AS (SELECT MAX(CASE WHEN business_line='products' THEN net_sales END) p,
 MAX(CASE WHEN business_line='services' THEN net_sales END) s,
 MAX(CASE WHEN business_line='products' THEN (net_sales-cost_of_sales)/net_sales END) pm,
 MAX(CASE WHEN business_line='services' THEN (net_sales-cost_of_sales)/net_sales END) sm FROM business_lines),
 r AS (SELECT g.*,s.products_loss_pct/100.0 pr,s.services_loss_pct/100.0 sr,
 ROW_NUMBER() OVER(ORDER BY g.geography) rn FROM geographies g JOIN stress_rates s USING(geography)) , objectives AS (
 SELECT 'revenue' measure,1.0 pw,1.0 sw,p+s base,s FROM lines UNION ALL
 SELECT 'gross_profit',pm,sm,p*pm+s*sm,s FROM lines),
 slopes AS (SELECT o.*,r.geography,r.net_sales cap,r.pr*o.pw intercept,r.pr*o.pw-r.sr*o.sw slope
 FROM objectives o CROSS JOIN r),
 directions AS (SELECT 'lower' endpoint,-1 direction UNION ALL SELECT 'upper',1),
 ranked AS (SELECT slopes.*,d.endpoint,
 COALESCE(SUM(cap) OVER(PARTITION BY measure,d.endpoint ORDER BY d.direction*slope,geography
 ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) used FROM slopes CROSS JOIN directions d),
 losses AS (SELECT measure,endpoint,base,SUM(cap*intercept-MAX(0,MIN(cap,s-used))*slope) loss
 FROM ranked GROUP BY measure,endpoint,base)
 SELECT measure,MAX(CASE WHEN endpoint='lower' THEN loss END) lower_usd_million,
 MAX(CASE WHEN endpoint='upper' THEN loss END) upper_usd_million,
 100.0*MAX(CASE WHEN endpoint='lower' THEN loss END)/base lower_pct,
 100.0*MAX(CASE WHEN endpoint='upper' THEN loss END)/base upper_pct FROM losses GROUP BY measure,base
