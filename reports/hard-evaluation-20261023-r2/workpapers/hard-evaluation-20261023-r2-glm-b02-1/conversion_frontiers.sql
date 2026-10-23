WITH
trigger_value AS (
  SELECT valuation FROM trigger
),
pref AS (
  SELECT p.series,
         p.shares,
         t.issue_price,
         t.preference_multiple,
         t.conversion_ratio,
         t.forced_eligible,
         p.shares * t.issue_price * t.preference_multiple / 1000000.0 AS pref_usd_m,
         t.issue_price * t.preference_multiple / t.conversion_ratio AS pref_per_conv
  FROM preferred p
  JOIN terms t ON t.series = p.series
),
frontier AS (
  SELECT f.series,
         f.pref_per_conv,
         (SELECT sum(shares) FROM common)
         + SUM(CASE WHEN p.forced_eligible = 1 OR p.pref_per_conv < f.pref_per_conv
                    OR p.series = f.series
                    THEN p.shares * p.conversion_ratio ELSE 0 END) AS shares_with_forced,
         SUM(CASE WHEN p.forced_eligible = 1 OR p.pref_per_conv < f.pref_per_conv
                    OR p.series = f.series
                  THEN 0 ELSE p.pref_usd_m END) AS retained_with_forced,
         SUM(CASE WHEN p.pref_per_conv < f.pref_per_conv
                    OR p.series = f.series
                  THEN p.shares * p.conversion_ratio ELSE 0 END) AS shares_without_forced,
         SUM(CASE WHEN p.series = f.series THEN 0
                  WHEN p.forced_eligible = 1
                    OR p.pref_per_conv >= f.pref_per_conv
                  THEN p.pref_usd_m ELSE 0 END) AS retained_without_forced
  FROM pref f
  CROSS JOIN pref p
  GROUP BY f.series
)
SELECT f.series,
       CASE
         WHEN f.pref_per_conv * f.shares_with_forced / 1000000.0
              + f.retained_with_forced > v.valuation
         THEN f.pref_per_conv * f.shares_with_forced / 1000000.0
              + f.retained_with_forced
         ELSE f.pref_per_conv * f.shares_without_forced / 1000000.0
              + f.retained_without_forced
       END AS proceeds_usd_million,
       f.pref_per_conv AS common_payout_per_share
FROM frontier f
CROSS JOIN trigger_value v
WHERE f.series IN (SELECT series FROM pref WHERE forced_eligible = 0)
ORDER BY f.series;
