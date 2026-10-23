-- Cash permits D <= surplus + (1-rate)*B.
-- When B >= trigger_draw, the covenant also requires D <= headroom-rate*B.
-- Optimize each linear branch at its endpoints or at the intersection.
-- The exempt branch has an open endpoint whenever B = trigger_draw.
WITH inputs AS (
    SELECT p.scenario, p.new_debt_cash_rate AS rate,
           p.working_capital_outflow AS crossing_draw,
           f.commitment - f.utilised_including_lc AS capacity,
           f.covenant_availability - f.test_threshold AS trigger_draw,
           p.ebitda - p.net_cash_capex - p.scheduled_principal
             - p.existing_cash_interest - p.cash_tax - p.ordinary_dividend AS headroom
    FROM planning_cases p CROSS JOIN facility f
), base AS (
    SELECT *, headroom - crossing_draw AS surplus
    FROM inputs
), exempt_points AS (
    SELECT *, 0.0 AS draw FROM base WHERE capacity >= 0 AND trigger_draw > 0
    UNION ALL
    SELECT *, MIN(capacity, trigger_draw) AS draw
    FROM base WHERE capacity >= 0 AND trigger_draw > 0
), exempt_values AS (
    SELECT *, surplus + (1.0-rate)*draw AS dividend
    FROM exempt_points
), exempt_candidates AS (
    SELECT scenario, dividend,
           CASE WHEN draw < trigger_draw THEN 1 ELSE 0 END AS attained
    FROM exempt_values
    WHERE dividend >= 0
      -- A zero limit approached from negative dividends is not feasible.
      AND (draw < trigger_draw OR dividend > 0 OR rate >= 1)
), tested_bounds AS (
    SELECT *, MAX(0.0, trigger_draw) AS lower_draw, capacity AS upper_draw
    FROM base
    WHERE capacity >= MAX(0.0, trigger_draw)
), tested_points AS (
    SELECT *, lower_draw AS draw FROM tested_bounds
    UNION ALL
    SELECT *, upper_draw AS draw FROM tested_bounds
    UNION ALL
    SELECT *, crossing_draw AS draw FROM tested_bounds
    WHERE crossing_draw BETWEEN lower_draw AND upper_draw
), tested_values AS (
    SELECT scenario,
           MIN(surplus + (1.0-rate)*draw, headroom-rate*draw) AS dividend,
           1 AS attained
    FROM tested_points
), candidates AS (
    SELECT scenario, dividend, attained FROM exempt_candidates
    UNION ALL
    SELECT scenario, dividend, attained FROM tested_values WHERE dividend >= 0
), limits AS (
    SELECT scenario, MAX(dividend) AS upper_limit
    FROM candidates GROUP BY scenario
)
SELECT b.scenario, l.upper_limit AS upper_limit_usd_million,
       COALESCE(MAX(c.attained), 0) AS attainable
FROM base b
LEFT JOIN limits l ON l.scenario = b.scenario
LEFT JOIN candidates c ON c.scenario = l.scenario AND c.dividend = l.upper_limit
GROUP BY b.scenario, l.upper_limit;
