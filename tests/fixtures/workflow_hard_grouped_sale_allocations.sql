WITH RECURSIVE terms_full AS (
 SELECT p.*,t.issue_price,t.preference_multiple,t.conversion_ratio,t.rank,t.forced_eligible,
 p.shares*t.issue_price*t.preference_multiple/1000000.0 preference,
 p.shares*t.conversion_ratio/1000000.0 converted
 FROM preferred p JOIN terms t USING(series)
), common_count AS (SELECT SUM(shares)/1000000.0 shares FROM common)
, cases AS (
 SELECT s.*,s.proceeds>t.valuation forced FROM sale_cases s CROSS JOIN trigger t
), remaining AS (
 SELECT c.sale_case,c.proceeds,n.* FROM cases c CROSS JOIN terms_full n
 WHERE NOT(c.forced=1 AND n.forced_eligible=1)
), totals AS (
 SELECT c.*,b.shares+COALESCE((SELECT SUM(n.converted) FROM terms_full n
 WHERE c.forced=1 AND n.forced_eligible=1),0) base,
 COALESCE((SELECT SUM(preference) FROM remaining r WHERE r.sale_case=c.sale_case),0) preference_total
 FROM cases c CROSS JOIN common_count b
), numbered AS (
 SELECT r.*,ROW_NUMBER() OVER(PARTITION BY sale_case ORDER BY series)-1 position FROM remaining r
), masks(mask) AS (SELECT 0 UNION ALL SELECT mask+1 FROM masks WHERE mask<511), prices AS (
 SELECT sale_case,MAX(0.0,MIN(price)) price FROM (
 SELECT t.sale_case,m.mask,(t.proceeds-t.preference_total+
 SUM(CASE WHEN (m.mask & (1 << n.position))!=0 THEN n.preference ELSE 0 END))/
 (t.base+SUM(CASE WHEN (m.mask & (1 << n.position))!=0 THEN n.converted ELSE 0 END)) price
 FROM totals t CROSS JOIN masks m JOIN numbered n USING(sale_case)
 GROUP BY t.sale_case,m.mask,t.proceeds,t.preference_total,t.base
 ) GROUP BY sale_case
), payments AS (
 SELECT c.sale_case,n.series security,n.shares,
 CASE WHEN c.forced=1 AND n.forced_eligible=1 THEN n.converted*p.price
 WHEN c.proceeds>=t.preference_total THEN MAX(n.preference,n.converted*p.price)
 ELSE MIN(n.preference,MAX(0.0,c.proceeds-COALESCE((SELECT SUM(r.preference)
 FROM remaining r WHERE r.sale_case=c.sale_case AND r.rank<n.rank),0))*n.preference/
 (SELECT SUM(r.preference) FROM remaining r WHERE r.sale_case=c.sale_case AND r.rank=n.rank)) END cash
 FROM cases c CROSS JOIN terms_full n JOIN prices p USING(sale_case) JOIN totals t USING(sale_case)
 UNION ALL SELECT p.sale_case,c.security,c.shares,c.shares/1000000.0*p.price FROM prices p CROSS JOIN common c
) SELECT sale_case,security,cash cash_usd_million,cash*1000000.0/shares payout_per_share FROM payments
