WITH instruments AS (
 SELECT n.*,t.conversion_rate,t.principal_settlement,
 n.principal*t.conversion_rate/1000.0 full_shares
 FROM notes n JOIN contract_terms t USING(note)
) SELECT p.price_case,n.note,
 CASE WHEN principal_settlement='cash' OR full_shares*p.price<=principal
 THEN principal ELSE 0.0 END cash_usd_million,
 CASE WHEN principal_settlement='cash' THEN MAX(0.0,full_shares-principal/p.price)
 WHEN full_shares*p.price>principal THEN full_shares ELSE 0.0 END gross_shares_million
 FROM instruments n CROSS JOIN price_cases p
