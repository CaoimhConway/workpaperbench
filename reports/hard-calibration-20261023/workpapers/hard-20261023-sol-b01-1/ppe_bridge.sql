WITH movements AS (
    SELECT
        (ending.capital_payables_billion - beginning.capital_payables_billion)
            * 1000.0 AS payables_change,
        c.cash_ppe,
        a.finance_rou_additions AS lease_additions,
        a.ppe_depreciation_billion * 1000.0 AS depreciation,
        ending.net - beginning.net AS net_change
    FROM ppe AS ending
    JOIN ppe AS beginning ON beginning.year = ending.year - 1
    JOIN cash_flows AS c ON c.year = ending.year
    JOIN annual_expenses AS a ON a.year = ending.year
    WHERE ending.year = 2025
), bridge AS (
    SELECT *,
        cash_ppe + payables_change AS purchase_proxy,
        cash_ppe + payables_change + lease_additions - depreciation
            AS explained_change
    FROM movements
)
SELECT
    payables_change AS payables_change_usd_million,
    purchase_proxy AS purchase_proxy_usd_million,
    lease_additions AS lease_additions_usd_million,
    depreciation AS depreciation_usd_million,
    net_change AS net_change_usd_million,
    explained_change AS explained_change_usd_million,
    net_change - explained_change AS residual_usd_million
FROM bridge;
