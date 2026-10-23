-- All aggregate money and share quantities below are in millions.
-- strike is USD per converted common share; preferences use charter terms.
WITH
capital AS (
  SELECT p.series, p.shares, t.forced_eligible, t.rank,
         p.shares * t.conversion_ratio / 1000000.0 AS converted_m,
         p.shares * t.issue_price * t.preference_multiple / 1000000.0 AS pref_m,
         t.issue_price * t.preference_multiple / t.conversion_ratio AS strike
  FROM preferred p JOIN terms t USING (series)
),
regimes AS (SELECT 0 AS mandatory UNION ALL SELECT 1),
remaining AS (
  SELECT g.mandatory, c.*
  FROM regimes g JOIN capital c ON g.mandatory = 0 OR c.forced_eligible = 0
),
totals AS (
  SELECT g.mandatory,
         (SELECT SUM(shares) / 1000000.0 FROM common)
           + SUM(CASE WHEN g.mandatory = 1 AND c.forced_eligible <> 0
                      THEN c.converted_m ELSE 0 END) AS base_common_m,
         SUM(CASE WHEN g.mandatory = 0 OR c.forced_eligible = 0
                  THEN c.pref_m ELSE 0 END) AS total_pref_m
  FROM regimes g CROSS JOIN capital c GROUP BY g.mandatory
),
nodes AS (
  SELECT mandatory, 0.0 AS common_price FROM regimes
  UNION
  SELECT mandatory, strike FROM remaining
),
-- Each line describes the common-price interval starting at its node.
-- Total proceeds there equal reserve_m + denominator_m * common_price.
lines AS (
  SELECT n.mandatory, n.common_price,
         z.base_common_m + COALESCE(SUM(
           CASE WHEN r.strike <= n.common_price THEN r.converted_m ELSE 0 END
         ), 0) AS denominator_m,
         COALESCE(SUM(
           CASE WHEN r.strike > n.common_price THEN r.pref_m ELSE 0 END
         ), 0) AS reserve_m
  FROM nodes n JOIN totals z USING (mandatory)
  LEFT JOIN remaining r ON r.mandatory = n.mandatory
  GROUP BY n.mandatory, n.common_price
),
segments AS (
  SELECT *, LEAD(common_price) OVER (
    PARTITION BY mandatory ORDER BY common_price
  ) AS next_price FROM lines
),
rank_sums AS (
  SELECT mandatory, rank, SUM(pref_m) AS rank_pref_m
  FROM remaining GROUP BY mandatory, rank
),
rank_bounds AS (
  SELECT *, COALESCE(SUM(rank_pref_m) OVER (
    PARTITION BY mandatory ORDER BY rank
    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
  ), 0.0) AS prior_m FROM rank_sums
),
frontiers AS (
  SELECT r.mandatory, r.series, r.strike,
         z.base_common_m * r.strike
           + SUM(MAX(o.pref_m, o.converted_m * r.strike)) AS proceeds_m
  FROM remaining r JOIN totals z USING (mandatory)
  JOIN remaining o ON o.mandatory = r.mandatory
  GROUP BY r.mandatory, r.series
)

SELECT f.series, f.proceeds_m AS proceeds_usd_million,
       f.strike AS common_payout_per_share
FROM frontiers f JOIN capital c USING (series) CROSS JOIN trigger t
WHERE c.forced_eligible = 0
  AND ((f.mandatory = 0 AND f.proceeds_m <= t.valuation)
    OR (f.mandatory = 1 AND f.proceeds_m > t.valuation))
ORDER BY f.series;
