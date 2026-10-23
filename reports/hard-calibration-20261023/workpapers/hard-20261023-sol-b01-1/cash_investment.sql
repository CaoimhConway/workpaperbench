SELECT
    c.cash_ppe AS cash_ppe_usd_million,
    a.finance_principal_cash AS principal_usd_million,
    c.cash_ppe + a.finance_principal_cash AS capital_cash_usd_million,
    a.finance_rou_additions AS noncash_lease_additions_usd_million
FROM cash_flows AS c
JOIN annual_expenses AS a ON a.year = c.year
WHERE c.year = 2025;
