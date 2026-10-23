WITH terms_full AS (
 SELECT p.*,t.issue_price,t.preference_multiple,t.conversion_ratio,t.rank,t.forced_eligible,
 p.shares*t.issue_price*t.preference_multiple/1000000.0 preference,
 p.shares*t.conversion_ratio/1000000.0 converted
 FROM preferred p JOIN terms t USING(series)
), common_count AS (SELECT SUM(shares)/1000000.0 shares FROM common)
, modes(forced) AS (SELECT 0 UNION ALL SELECT 1), branch_totals AS (
 SELECT m.forced,b.shares+SUM(CASE WHEN m.forced=1 AND t.forced_eligible=1
 THEN t.converted ELSE 0.0 END) base FROM modes m CROSS JOIN common_count b CROSS JOIN terms_full t
 GROUP BY m.forced,b.shares
), remaining AS (
 SELECT m.forced,t.* FROM modes m CROSS JOIN terms_full t WHERE NOT(m.forced=1 AND t.forced_eligible=1)
)
, owners AS (
 SELECT series security,converted quantity FROM terms_full
 UNION ALL SELECT security,shares/1000000.0 FROM common
), candidates AS (
 SELECT q.target_case,b.forced,
 CASE WHEN h.series IS NOT NULL AND q.cash_target<=h.preference THEN
 COALESCE((SELECT SUM(r.preference) FROM remaining r WHERE r.forced=b.forced AND r.rank<h.rank),0)
 +q.cash_target/h.preference*(SELECT SUM(r.preference) FROM remaining r WHERE r.forced=b.forced AND r.rank=h.rank)
 ELSE b.base*q.cash_target/o.quantity+(SELECT SUM(MAX(r.preference,r.converted*q.cash_target/o.quantity))
 FROM remaining r WHERE r.forced=b.forced) END required
 FROM owner_targets q JOIN owners o USING(security) CROSS JOIN branch_totals b
 LEFT JOIN remaining h ON h.forced=b.forced AND h.series=q.security
), feasible AS (
 SELECT c.target_case,CASE WHEN forced=1 THEN MAX(required,t.valuation) ELSE required END value,
 CASE WHEN forced=0 OR required>t.valuation THEN 1 ELSE 0 END attained
 FROM candidates c CROSS JOIN trigger t WHERE forced=1 OR required<=t.valuation
), minima AS (SELECT target_case,MIN(value) value FROM feasible GROUP BY target_case)
 SELECT m.target_case,m.value proceeds_infimum_usd_million,MAX(f.attained) attained
 FROM minima m JOIN feasible f ON f.target_case=m.target_case AND f.value=m.value
 GROUP BY m.target_case,m.value
