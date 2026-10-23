WITH fy_cash AS (
    SELECT cash_ppe
    FROM cash_flows
    WHERE year = 2025
),
fy_lease AS (
    SELECT finance_principal_cash, finance_rou_additions
    FROM annual_expenses
    WHERE year = 2025
)
SELECT
    c.cash_ppe AS cash_ppe_usd_million,
    l.finance_principal_cash AS principal_usd_million,
    c.cash_ppe + l.finance_principal_cash AS capital_cash_usd_million,
    l.finance_rou_additions AS noncash_lease_additions_usd_million
FROM fy_cash AS c
CROSS JOIN fy_lease AS l;
