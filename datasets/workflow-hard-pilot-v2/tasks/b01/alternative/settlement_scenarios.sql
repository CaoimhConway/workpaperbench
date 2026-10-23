WITH instruments AS (
 SELECT n.*,t.conversion_rate,t.principal_settlement,
 n.principal*t.conversion_rate/1000.0 full_shares
 FROM notes n JOIN contract_terms t USING(note)
) , values_at_price AS (
 SELECT p.price_case,n.*,p.price,MAX(principal,full_shares*p.price) holder_value
 FROM instruments n CROSS JOIN price_cases p
), funding AS (
 SELECT *,CASE WHEN principal_settlement='cash' OR holder_value=principal
 THEN principal ELSE 0.0 END funded FROM values_at_price
) SELECT price_case,note,funded cash_usd_million,
 (holder_value-funded)/price gross_shares_million FROM funding
