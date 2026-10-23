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
) , ordered AS (
 SELECT price_case,note,shares,adjustment,
 SUM(shares) OVER(PARTITION BY price_case ORDER BY adjustment/shares,note
 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) cumulative_shares,
 SUM(adjustment) OVER(PARTITION BY price_case ORDER BY adjustment/shares,note
 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) cumulative_adjustment
 FROM components WHERE shares>0
), candidates AS (
 SELECT p.price_case,i.income_case,i.income/b.basic_shares basic_eps,
 i.income/(b.basic_shares+b.award_shares) eps
 FROM price_cases p CROSS JOIN income_cases i CROSS JOIN eps_basis b
 UNION ALL SELECT o.price_case,i.income_case,i.income/b.basic_shares,
 (i.income+cumulative_adjustment)/(b.basic_shares+b.award_shares+cumulative_shares)
 FROM ordered o CROSS JOIN income_cases i CROSS JOIN eps_basis b
) SELECT price_case,income_case,basic_eps,MIN(eps) diluted_eps
 FROM candidates GROUP BY price_case,income_case,basic_eps
