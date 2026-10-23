-- For target D and borrowing B, required equity is
-- max(0, D-surplus-(1-rate)*B). Equity does not cure the covenant.
-- Optimize on the exempt open interval and the tested closed interval.
WITH inputs AS (
    SELECT p.scenario, t.target, t.special_dividend,
           p.new_debt_cash_rate AS rate,
           f.commitment - f.utilised_including_lc AS capacity,
           f.covenant_availability - f.test_threshold AS trigger_draw,
           p.ebitda - p.net_cash_capex - p.scheduled_principal
             - p.existing_cash_interest - p.cash_tax - p.ordinary_dividend AS headroom,
           p.working_capital_outflow AS working_capital
    FROM planning_cases p CROSS JOIN equity_targets t CROSS JOIN facility f
), base AS (
    SELECT *, headroom - working_capital AS surplus
    FROM inputs
), exempt_points AS (
    SELECT *, 0.0 AS draw FROM base WHERE capacity >= 0 AND trigger_draw > 0
    UNION ALL
    SELECT *, MIN(capacity, trigger_draw) AS draw
    FROM base WHERE capacity >= 0 AND trigger_draw > 0
), exempt_values AS (
    SELECT *, special_dividend - surplus - (1.0-rate)*draw AS raw_equity
    FROM exempt_points
), exempt_candidates AS (
    SELECT scenario, target, MAX(0.0, raw_equity) AS equity,
           -- Strict cash surplus at the boundary allows zero equity at
           -- a nearby interior draw. Equality alone does not suffice.
           CASE WHEN draw < trigger_draw OR raw_equity < 0 THEN 1 ELSE 0 END AS attained
    FROM exempt_values
), tested_bounds AS (
    SELECT *,
           CASE WHEN rate < 0
                THEN MAX(0.0, trigger_draw, (headroom-special_dividend)/rate)
                ELSE MAX(0.0, trigger_draw) END AS lower_draw,
           CASE WHEN rate > 0
                THEN MIN(capacity, (headroom-special_dividend)/rate)
                ELSE capacity END AS upper_draw
    FROM base
    WHERE rate <> 0 OR headroom >= special_dividend
), tested_points AS (
    SELECT *, lower_draw AS draw FROM tested_bounds WHERE lower_draw <= upper_draw
    UNION ALL
    SELECT *, upper_draw AS draw FROM tested_bounds WHERE lower_draw <= upper_draw
), tested_candidates AS (
    SELECT scenario, target,
           MAX(0.0, special_dividend-surplus-(1.0-rate)*draw) AS equity,
           1 AS attained
    FROM tested_points
), candidates AS (
    SELECT * FROM exempt_candidates
    UNION ALL
    SELECT * FROM tested_candidates
), limits AS (
    SELECT scenario, target, MIN(equity) AS lower_limit
    FROM candidates GROUP BY scenario, target
)
SELECT b.scenario, b.target, l.lower_limit AS lower_limit_usd_million,
       COALESCE(MAX(c.attained), 0) AS attainable
FROM base b
LEFT JOIN limits l ON l.scenario = b.scenario AND l.target = b.target
LEFT JOIN candidates c ON c.scenario = l.scenario AND c.target = l.target
                          AND c.equity = l.lower_limit
GROUP BY b.scenario, b.target, l.lower_limit;
