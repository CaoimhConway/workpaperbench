WITH cash AS (
    SELECT period, operating, collateral, capex
    FROM cash_flows
), policy AS (
    SELECT period, basis
    FROM facility_policy
), facility AS (
    SELECT period, dpp_collections, purchaser_payment
    FROM facility_flows
), recast AS (
    SELECT
        c.period,
        CASE
            WHEN p.basis = 'sale'
            THEN c.operating + COALESCE(f.dpp_collections, 0.0)
            ELSE c.operating
        END AS normalized_operating,
        c.collateral,
        c.capex
    FROM cash AS c
    LEFT JOIN policy AS p ON p.period = c.period
    LEFT JOIN facility AS f ON f.period = c.period
), periods AS (
    SELECT
        (SELECT operating FROM cash WHERE period = '2025-9m') AS reported_2025,
        (SELECT operating FROM cash WHERE period = '2024-9m') AS reported_2024,
        (SELECT normalized_operating FROM recast WHERE period = '2025-9m') AS normalized_2025,
        (SELECT normalized_operating FROM recast WHERE period = '2024-9m') AS normalized_2024,
        (SELECT collateral FROM cash WHERE period = '2025-9m') AS collateral_2025,
        (SELECT collateral FROM cash WHERE period = '2024-9m') AS collateral_2024,
        (SELECT capex FROM cash WHERE period = '2025-9m') AS capex_2025,
        (SELECT capex FROM cash WHERE period = '2024-9m') AS capex_2024
), changes AS (
    SELECT
        reported_2025 - reported_2024 AS reported_operating_change,
        normalized_2025 - normalized_2024 AS normalized_operating_change,
        collateral_2025 - collateral_2024 AS collateral_change,
        (normalized_2025 - collateral_2025)
          - (normalized_2024 - collateral_2024) AS other_operating_change,
        (normalized_2025 - capex_2025)
          - (normalized_2024 - capex_2024) AS normalized_after_capex_change,
        ((normalized_2025 - collateral_2025) - capex_2025)
          - ((normalized_2024 - collateral_2024) - capex_2024) AS other_after_capex_change
    FROM periods
)
SELECT
    reported_operating_change,
    normalized_operating_change,
    reported_operating_change - normalized_operating_change AS presentation_effect,
    collateral_change,
    other_operating_change,
    normalized_after_capex_change,
    other_after_capex_change
FROM changes;
