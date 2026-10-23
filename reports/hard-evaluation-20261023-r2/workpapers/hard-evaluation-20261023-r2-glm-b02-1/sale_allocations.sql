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
         t.rank,
         t.forced_eligible,
         p.shares * t.issue_price * t.preference_multiple / 1000000.0 AS pref_usd_m,
         t.issue_price * t.preference_multiple / t.conversion_ratio AS pref_per_conv
  FROM preferred p
  JOIN terms t ON t.series = p.series
),
common_total AS (
  SELECT sum(shares) AS shares FROM common
),
hypothetical AS (
  SELECT cs.sale_case,
         f.series AS series,
         sum(CASE
           WHEN p.forced_eligible = 1 AND cs.proceeds > v.valuation THEN 0
           WHEN p.forced_eligible = 0
                AND (p.pref_per_conv < f.pref_per_conv OR p.series = f.series)
           THEN 0 ELSE p.pref_usd_m END) AS retained_pref,
         ct.shares + sum(CASE
           WHEN p.forced_eligible = 1 AND cs.proceeds > v.valuation
           THEN p.shares * p.conversion_ratio
           WHEN p.forced_eligible = 0
                AND (p.pref_per_conv < f.pref_per_conv OR p.series = f.series)
           THEN p.shares * p.conversion_ratio ELSE 0 END) AS common_shares
  FROM sale_cases cs
  CROSS JOIN pref f
  CROSS JOIN pref p
  CROSS JOIN trigger_value v
  CROSS JOIN common_total ct
  GROUP BY cs.sale_case, f.series
),
hyp_values AS (
  SELECT sale_case,
         series,
         max(sale_case_retained.retained_pref, 0) AS placeholder
  FROM hypothetical sale_case_retained
),
status AS (
  SELECT cs.sale_case,
         cs.proceeds,
         p.series,
         p.shares,
         p.conversion_ratio,
         p.pref_usd_m,
         p.rank,
         CASE
           WHEN p.forced_eligible = 1 THEN cs.proceeds > v.valuation
           ELSE h.common_per_share >= p.pref_per_conv
         END AS converted
  FROM sale_cases cs
  CROSS JOIN trigger_value v
  JOIN pref p
  LEFT JOIN (
    SELECT h.sale_case,
           h.series,
           max(cs.proceeds - h.retained_pref, 0) * 1000000.0
             / h.common_shares AS common_per_share
    FROM hypothetical h
    JOIN sale_cases cs ON cs.sale_case = h.sale_case
    GROUP BY h.sale_case, h.series
  ) h ON h.sale_case = cs.sale_case AND h.series = p.series
),
state AS (
  SELECT sale_case,
         proceeds,
         sum(CASE WHEN rank = 1 AND converted = 0
                  THEN pref_usd_m ELSE 0 END) AS rank1_pref,
         sum(CASE WHEN rank = 2 AND converted = 0
                  THEN pref_usd_m ELSE 0 END) AS rank2_pref,
         ct.shares + sum(CASE WHEN converted = 1
                           THEN shares * conversion_ratio ELSE 0 END) AS common_shares
  FROM status
  CROSS JOIN common_total ct
  GROUP BY sale_case
),
state_alloc AS (
  SELECT sale_case,
         proceeds,
         rank1_pref,
         rank2_pref,
         min(proceeds, rank1_pref) AS rank1_take,
         min(max(proceeds - min(proceeds, rank1_pref), 0), rank2_pref) AS rank2_take,
         max(proceeds - min(proceeds, rank1_pref)
             - min(max(proceeds - min(proceeds, rank1_pref), 0), rank2_pref), 0)
           * 1000000.0 / common_shares AS common_per_share
  FROM state
),
preferred_alloc AS (
  SELECT s.sale_case,
         s.series AS security,
         CASE
           WHEN s.converted = 1
             THEN s.shares * s.conversion_ratio * a.common_per_share / 1000000.0
           WHEN s.rank = 1
             THEN s.pref_usd_m * a.rank1_take / a.rank1_pref
           ELSE s.pref_usd_m * a.rank2_take / a.rank2_pref
         END AS cash_usd_million
  FROM status s
  JOIN state_alloc a ON a.sale_case = s.sale_case
),
common_alloc AS (
  SELECT a.sale_case,
         c.security,
         c.shares * a.common_per_share / 1000000.0 AS cash_usd_million
  FROM state_alloc a
  CROSS JOIN common c
),
allocation AS (
  SELECT * FROM preferred_alloc
  UNION ALL
  SELECT * FROM common_alloc
)
SELECT a.sale_case AS sale_case,
       a.security AS security,
       a.cash_usd_million AS cash_usd_million,
       a.cash_usd_million * 1000000.0
         / coalesce(p.shares, c.shares) AS payout_per_share
FROM allocation a
LEFT JOIN pref p ON p.series = a.security
LEFT JOIN common c ON c.security = a.security
ORDER BY a.sale_case, a.security;
