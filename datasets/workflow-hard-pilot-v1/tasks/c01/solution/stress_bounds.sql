WITH lines AS (SELECT MAX(CASE WHEN business_line='products' THEN net_sales END) p,
 MAX(CASE WHEN business_line='services' THEN net_sales END) s,
 MAX(CASE WHEN business_line='products' THEN (net_sales-cost_of_sales)/net_sales END) pm,
 MAX(CASE WHEN business_line='services' THEN (net_sales-cost_of_sales)/net_sales END) sm FROM business_lines),
 r AS (SELECT g.*,s.products_loss_pct/100.0 pr,s.services_loss_pct/100.0 sr,
 ROW_NUMBER() OVER(ORDER BY g.geography) rn FROM geographies g JOIN stress_rates s USING(geography)) , limits AS (SELECT 0 bound UNION ALL SELECT 1),
 candidates AS (SELECT a.geography ga,b.geography gb,c.geography gc,
 a.net_sales*x.bound sa,b.net_sales*y.bound sb,s-a.net_sales*x.bound-b.net_sales*y.bound sc
 FROM r a JOIN r b ON a.rn<b.rn JOIN r c ON c.rn!=a.rn AND c.rn!=b.rn
 CROSS JOIN limits x CROSS JOIN limits y CROSS JOIN lines
 WHERE s-a.net_sales*x.bound-b.net_sales*y.bound BETWEEN 0 AND c.net_sales),
 objectives AS (SELECT 'revenue' measure,1.0 pw,1.0 sw,p+s base FROM lines UNION ALL
 SELECT 'gross_profit',pm,sm,p*pm+s*sm FROM lines),
 losses AS (SELECT o.measure,o.base,v.ga,v.gb,v.gc,v.sa,v.sb,v.sc,
 SUM((r.net_sales-CASE r.geography WHEN v.ga THEN v.sa WHEN v.gb THEN v.sb ELSE v.sc END)*r.pr*o.pw+
 (CASE r.geography WHEN v.ga THEN v.sa WHEN v.gb THEN v.sb ELSE v.sc END)*r.sr*o.sw) loss
 FROM candidates v CROSS JOIN r CROSS JOIN objectives o GROUP BY o.measure,o.base,v.ga,v.gb,v.gc,v.sa,v.sb,v.sc)
 SELECT measure,MIN(loss) lower_usd_million,MAX(loss) upper_usd_million,
 100.0*MIN(loss)/base lower_pct,100.0*MAX(loss)/base upper_pct FROM losses GROUP BY measure,base
