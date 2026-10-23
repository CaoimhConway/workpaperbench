WITH instruments AS (
 SELECT n.*,t.conversion_rate,t.principal_settlement,
 n.principal*t.conversion_rate/1000.0 full_shares
 FROM notes n JOIN contract_terms t USING(note)
) , components AS (
 SELECT note,principal_settlement,
 CASE WHEN principal_settlement='cash' THEN MAX(0.0,full_shares-principal/q.price)
 ELSE full_shares END shares,
 CASE WHEN principal_settlement='cash' THEN 0.0 ELSE coupon+amortization END adjustment
 FROM instruments CROSS JOIN threshold_case q
), boundaries AS (
 SELECT c.note,c.adjustment/c.shares*(b.basic_shares+b.award_shares+
 COALESCE(SUM(o.shares),0))-COALESCE(SUM(o.adjustment),0) value
 FROM components c CROSS JOIN eps_basis b LEFT JOIN components o
 ON o.shares>0 AND o.adjustment*c.shares<c.adjustment*o.shares
 WHERE c.principal_settlement!='cash'
 GROUP BY c.note,c.adjustment,c.shares,b.basic_shares,b.award_shares
) SELECT 'earnings_'||note measure,value FROM boundaries UNION ALL
 SELECT 'share_price',SUM(CASE WHEN principal_settlement='cash' THEN principal ELSE 0 END)
 /(SUM(full_shares)-q.target_shares) FROM instruments CROSS JOIN threshold_case q
 GROUP BY q.target_shares
