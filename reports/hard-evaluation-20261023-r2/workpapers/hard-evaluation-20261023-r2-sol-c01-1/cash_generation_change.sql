-- USD million. Compare the two nine-month periods in sequence order.
-- Tariff sales retain their reported treatment. Collateral is signed;
-- capex is a positive payment magnitude. No cause is assigned to the
-- remaining collateral-neutral movement.
WITH normalized AS (
    SELECT c.period, c.sequence, c.operating, c.collateral, c.capex,
           c.operating + CASE WHEN p.basis = 'sale'
               THEN f.dpp_collections ELSE 0 END AS operating_cash
    FROM cash_flows AS c
    JOIN facility_policy AS p ON p.period = c.period
    LEFT JOIN facility_flows AS f ON f.period = c.period
), changes AS (
    SELECT b.operating - a.operating AS reported_change,
           b.operating_cash - a.operating_cash AS normalized_change,
           b.collateral - a.collateral AS collateral_change,
           b.capex - a.capex AS capex_change
    FROM normalized AS a
    JOIN normalized AS b ON b.sequence = a.sequence + 1
)
SELECT reported_change AS reported_operating_change,
       normalized_change AS normalized_operating_change,
       reported_change - normalized_change AS presentation_effect,
       collateral_change,
       normalized_change - collateral_change AS other_operating_change,
       normalized_change - capex_change AS normalized_after_capex_change,
       normalized_change - collateral_change - capex_change
           AS other_after_capex_change
FROM changes;
