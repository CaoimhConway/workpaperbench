WITH balances AS (
    SELECT
        ending.gross - beginning.gross AS gross_change,
        ending.accumulated - beginning.accumulated AS accumulated_change,
        ending.net - beginning.net AS net_change,
        a.finance_rou_additions AS additions,
        a.finance_amortization AS amortization
    FROM finance_leases AS ending
    JOIN finance_leases AS beginning ON beginning.year = ending.year - 1
    JOIN annual_expenses AS a ON a.year = ending.year
    WHERE ending.year = 2025
), movements AS (
    SELECT 'gross' AS measure, gross_change AS observed,
        additions AS explained FROM balances
    UNION ALL
    SELECT 'accumulated', accumulated_change, amortization FROM balances
    UNION ALL
    SELECT 'net', net_change, additions - amortization FROM balances
)
SELECT
    measure,
    observed AS change_usd_million,
    explained AS explained_change_usd_million,
    observed - explained AS residual_usd_million
FROM movements;
