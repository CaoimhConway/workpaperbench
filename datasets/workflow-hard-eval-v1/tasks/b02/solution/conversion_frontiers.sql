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
, candidates AS (
 SELECT n.series,b.forced,n.preference/n.converted price,
 b.base*n.preference/n.converted+SUM(MAX(r.preference,r.converted*n.preference/n.converted)) proceeds
 FROM terms_full n CROSS JOIN branch_totals b JOIN remaining r ON r.forced=b.forced
 WHERE n.forced_eligible=0 GROUP BY n.series,b.forced,n.preference,n.converted,b.base
) SELECT c.series,MIN(c.proceeds) proceeds_usd_million,c.price common_payout_per_share
 FROM candidates c CROSS JOIN trigger t WHERE (c.proceeds>t.valuation)=c.forced
 GROUP BY c.series,c.price
