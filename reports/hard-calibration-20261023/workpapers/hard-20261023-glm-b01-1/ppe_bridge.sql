WITH fy_cash AS (
    SELECT cash_ppe
    FROM cash_flows
    WHERE year = 2025
),
fy_expense AS (
    SELECT ppe_depreciation_billion, finance_rou_additions
    FROM annual_expenses
    WHERE year = 2025
),
ppe_begin AS (
    SELECT capital_payables_billion, net
    FROM ppe
    WHERE year = 2024
),
ppe_end AS (
    SELECT capital_payables_billion, net
    FROM ppe
    WHERE year = 2025
),
components AS (
    SELECT
        (e.capital_payables_billion - b.capital_payables_billion) * 1000.0 AS payables_change_usd_million,
        c.cash_ppe
          + (e.capital_payables_billion - b.capital_payables_billion) * 1000.0 AS purchase_proxy_usd_million,
        x.finance_rou_additions AS lease_additions_usd_million,
        x.ppe_depreciation_billion * 1000.0 AS depreciation_usd_million,
        e.net - b.net AS net_change_usd_million
    FROM fy_cash AS c
    CROSS JOIN fy_expense AS x
    CROSS JOIN ppe_begin AS b
    CROSS JOIN ppe_end AS e
)
SELECT
    payables_change_usd_million,
    purchase_proxy_usd_million,
    lease_additions_usd_million,
    depreciation_usd_million,
    net_change_usd_million,
    purchase_proxy_usd_million
      + lease_additions_usd_million
      - depreciation_usd_million AS explained_change_usd_million,
    net_change_usd_million
      - (purchase_proxy_usd_million
         + lease_additions_usd_million
         - depreciation_usd_million) AS residual_usd_million
FROM components;
