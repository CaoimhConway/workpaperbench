WITH instruments AS (
 SELECT n.*,t.conversion_rate,t.principal_settlement,
 n.principal*t.conversion_rate/1000.0 full_shares
 FROM notes n JOIN contract_terms t USING(note)
) , components AS (
 SELECT p.price_case,n.note,
 CASE WHEN principal_settlement='cash' THEN MAX(0.0,full_shares-principal/p.price)
 ELSE full_shares END shares,
 CASE WHEN principal_settlement='cash' THEN 0.0 ELSE coupon+amortization END adjustment,
 ROW_NUMBER() OVER(PARTITION BY p.price_case ORDER BY n.note) position
 FROM instruments n CROSS JOIN price_cases p
) , masks(mask) AS (
 SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7
), candidates AS (
 SELECT c.price_case,i.income_case,i.income,b.basic_shares,m.mask,
 i.income+SUM(CASE WHEN (m.mask & (1 << (c.position-1)))!=0 THEN adjustment ELSE 0 END) numerator,
 b.basic_shares+b.award_shares+
 SUM(CASE WHEN (m.mask & (1 << (c.position-1)))!=0 THEN shares ELSE 0 END) denominator
 FROM components c CROSS JOIN income_cases i CROSS JOIN eps_basis b CROSS JOIN masks m
 GROUP BY c.price_case,i.income_case,i.income,b.basic_shares,b.award_shares,m.mask
) SELECT price_case,income_case,income/basic_shares basic_eps,
 MIN(numerator/denominator) diluted_eps FROM candidates
 GROUP BY price_case,income_case,income,basic_shares
