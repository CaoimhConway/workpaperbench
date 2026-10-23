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
cohorts AS (
  SELECT series AS security, converted_m, strike, forced_eligible, 0 AS is_common
  FROM capital
  UNION ALL
  SELECT security, shares / 1000000.0, NULL, 0, 1 FROM common
),
-- Cash on every relevant piece is slope * proceeds + intercept_m.
-- Zero-cash pieces can be omitted because every target is positive.
pieces AS (
  -- Partial payment of the owner's preferred priority rank.
  SELECT o.target_case, o.cash_target, r.mandatory,
         b.prior_m AS lo, b.prior_m + b.rank_pref_m AS hi,
         r.pref_m / b.rank_pref_m AS slope,
         -r.pref_m * b.prior_m / b.rank_pref_m AS intercept_m
  FROM owner_targets o JOIN remaining r ON r.series = o.security
  JOIN rank_bounds b ON b.mandatory = r.mandatory AND b.rank = r.rank
  UNION ALL
  -- Full preference retained until voluntary conversion is indifferent.
  SELECT o.target_case, o.cash_target, r.mandatory,
         b.prior_m + b.rank_pref_m, f.proceeds_m, 0.0, r.pref_m
  FROM owner_targets o JOIN remaining r ON r.series = o.security
  JOIN rank_bounds b ON b.mandatory = r.mandatory AND b.rank = r.rank
  JOIN frontiers f ON f.mandatory = r.mandatory AND f.series = r.series
  UNION ALL
  -- Original common, mandatory converts, and voluntary converts.
  SELECT o.target_case, o.cash_target, s.mandatory,
         s.reserve_m + s.denominator_m * s.common_price,
         CASE WHEN s.next_price IS NULL THEN NULL
              ELSE s.reserve_m + s.denominator_m * s.next_price END,
         c.converted_m / s.denominator_m,
         -c.converted_m * s.reserve_m / s.denominator_m
  FROM owner_targets o JOIN cohorts c ON c.security = o.security
  JOIN segments s ON c.is_common = 1
       OR (s.mandatory = 1 AND c.forced_eligible <> 0)
       OR c.strike <= s.common_price
),
clipped AS (
  SELECT p.*, t.valuation,
         MAX(p.lo, CASE WHEN p.mandatory = 1 THEN t.valuation ELSE 0.0 END) AS lower_m,
         CASE WHEN p.mandatory = 0 THEN MIN(COALESCE(p.hi, t.valuation), t.valuation)
              ELSE p.hi END AS upper_m
  FROM pieces p CROSS JOIN trigger t
),
roots AS (
  SELECT *, CASE
    WHEN slope > 0 THEN MAX(lower_m, (cash_target - intercept_m) / slope)
    WHEN intercept_m >= cash_target THEN lower_m
    ELSE NULL END AS candidate_m
  FROM clipped
),
feasible AS (
  SELECT target_case, candidate_m,
         CASE WHEN mandatory = 1 AND candidate_m = valuation
              THEN 0 ELSE 1 END AS attained
  FROM roots
  WHERE candidate_m IS NOT NULL
    AND (upper_m IS NULL OR candidate_m <= upper_m)
    -- The mandatory-conversion regime is open at the trigger.
    AND (mandatory = 0 OR upper_m IS NULL OR upper_m > valuation)
),
infima AS (
  SELECT target_case, MIN(candidate_m) AS proceeds_infimum_usd_million
  FROM feasible GROUP BY target_case
)
SELECT i.target_case, i.proceeds_infimum_usd_million,
       MAX(f.attained) * 1.0 AS attained
FROM infima i JOIN feasible f ON f.target_case = i.target_case
 AND f.candidate_m = i.proceeds_infimum_usd_million
GROUP BY i.target_case, i.proceeds_infimum_usd_million
ORDER BY i.target_case;
