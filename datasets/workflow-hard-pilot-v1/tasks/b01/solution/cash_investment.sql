WITH b AS (SELECT c.cash_ppe,a.*,1000.0*(p.capital_payables_billion-o.capital_payables_billion) payable_change,
 p.net-o.net net_change FROM cash_flows c JOIN annual_expenses a USING(year)
 JOIN ppe p ON p.year=c.year JOIN ppe o ON o.year=c.year-1) SELECT cash_ppe cash_ppe_usd_million,finance_principal_cash principal_usd_million,
 cash_ppe+finance_principal_cash capital_cash_usd_million,finance_rou_additions noncash_lease_additions_usd_million FROM b
