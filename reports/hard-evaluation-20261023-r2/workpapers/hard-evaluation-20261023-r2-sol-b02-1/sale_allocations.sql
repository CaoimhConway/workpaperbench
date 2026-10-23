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
,
sale_states AS (
  SELECT s.*, CASE WHEN s.proceeds > t.valuation THEN 1 ELSE 0 END AS mandatory
  FROM sale_cases s CROSS JOIN trigger t
),
sale_prices AS (
  -- The proceeds function is convex, so its inverse is the minimum
  -- of the extended segment lines, floored at zero during shortfalls.
  SELECT s.sale_case, s.proceeds, s.mandatory, z.total_pref_m,
         MAX(0.0, MIN((s.proceeds - l.reserve_m) / l.denominator_m)) AS price
  FROM sale_states s JOIN lines l USING (mandatory)
  JOIN totals z USING (mandatory)
  GROUP BY s.sale_case
),
cohort_cash AS (
  SELECT s.sale_case, c.series AS security, c.shares,
         CASE
           WHEN s.mandatory = 1 AND c.forced_eligible <> 0
             THEN c.converted_m * s.price
           WHEN s.proceeds >= s.total_pref_m
             THEN MAX(c.pref_m, c.converted_m * s.price)
           ELSE c.pref_m * MIN(1.0, MAX(0.0,
                  (s.proceeds - b.prior_m) / b.rank_pref_m))
         END AS cash_usd_million
  FROM sale_prices s CROSS JOIN capital c
  LEFT JOIN rank_bounds b ON b.mandatory = s.mandatory AND b.rank = c.rank
  UNION ALL
  SELECT s.sale_case, c.security, c.shares,
         c.shares / 1000000.0 * s.price
  FROM sale_prices s CROSS JOIN common c
)
SELECT sale_case, security, cash_usd_million,
       cash_usd_million * 1000000.0 / shares AS payout_per_share
FROM cohort_cash
ORDER BY sale_case, security;
