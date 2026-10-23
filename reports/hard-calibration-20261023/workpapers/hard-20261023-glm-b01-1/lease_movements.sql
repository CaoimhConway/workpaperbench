WITH fy_expense AS (
    SELECT finance_rou_additions, finance_amortization
    FROM annual_expenses
    WHERE year = 2025
),
lease_begin AS (
    SELECT gross, accumulated, net
    FROM finance_leases
    WHERE year = 2024
),
lease_end AS (
    SELECT gross, accumulated, net
    FROM finance_leases
    WHERE year = 2025
),
base AS (
    SELECT
        x.finance_rou_additions,
        x.finance_amortization,
        b.gross AS begin_gross,
        b.accumulated AS begin_accumulated,
        b.net AS begin_net,
        e.gross AS end_gross,
        e.accumulated AS end_accumulated,
        e.net AS end_net
    FROM fy_expense AS x
    CROSS JOIN lease_begin AS b
    CROSS JOIN lease_end AS e
)
SELECT
    'gross' AS measure,
    end_gross - begin_gross AS change_usd_million,
    finance_rou_additions AS explained_change_usd_million,
    end_gross - begin_gross - finance_rou_additions AS residual_usd_million
FROM base
UNION ALL
SELECT
    'accumulated' AS measure,
    end_accumulated - begin_accumulated AS change_usd_million,
    finance_amortization AS explained_change_usd_million,
    end_accumulated - begin_accumulated - finance_amortization AS residual_usd_million
FROM base
UNION ALL
SELECT
    'net' AS measure,
    end_net - begin_net AS change_usd_million,
    finance_rou_additions - finance_amortization AS explained_change_usd_million,
    end_net - begin_net
      - (finance_rou_additions - finance_amortization) AS residual_usd_million
FROM base;
