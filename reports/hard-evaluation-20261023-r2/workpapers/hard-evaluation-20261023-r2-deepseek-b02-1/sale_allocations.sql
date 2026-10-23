WITH pref AS (
  SELECT t.series, p.shares, t.issue_price, t.rank, t.forced_eligible,
         t.issue_price * t.preference_multiple AS pps,
         (t.issue_price * t.preference_multiple * p.shares) / 1000000.0 AS pref_m
  FROM terms t JOIN preferred p ON p.series = t.series
), params AS (
  SELECT (SELECT valuation FROM trigger) AS trigger_v,
         (SELECT SUM(shares) FROM common) AS common_sh,
         (SELECT shares FROM common WHERE security='common_A') AS common_a_sh,
         (SELECT shares FROM common WHERE security='common_B') AS common_b_sh,
         (SELECT pref_m FROM pref WHERE series='A-1') AS a1_pref
), front AS (
  SELECT o.series,
         (SELECT COALESCE(SUM(h.pref_m),0) FROM pref h
           WHERE h.rank=1 AND h.forced_eligible=0 AND h.issue_price > o.issue_price)
         + o.pps * ((SELECT common_sh FROM params)
                    + (SELECT COALESCE(SUM(f.shares),0) FROM pref f WHERE f.forced_eligible=1)
                    + (SELECT COALESCE(SUM(l.shares),0) FROM pref l
                        WHERE l.forced_eligible=0 AND l.issue_price <= o.issue_price)) / 1000000.0 AS frontier_m
  FROM pref o WHERE o.forced_eligible=0
), conv AS (
  SELECT s.sale_case, f.series
    FROM sale_cases s JOIN front f ON s.proceeds >= f.frontier_m
  UNION
  SELECT s.sale_case, p.series
    FROM sale_cases s CROSS JOIN params x JOIN pref p ON p.forced_eligible=1
   WHERE s.proceeds > x.trigger_v
), state AS (
  SELECT s.sale_case, s.proceeds,
         (SELECT COALESCE(SUM(p.shares),0) FROM pref p
           JOIN conv c ON c.sale_case=s.sale_case AND c.series=p.series) AS conv_sh,
         (SELECT COALESCE(SUM(p.pref_m),0) FROM pref p
           WHERE p.rank=1
             AND NOT EXISTS (SELECT 1 FROM conv c WHERE c.sale_case=s.sale_case AND c.series=p.series)) AS rank1_rem,
         CASE WHEN EXISTS (SELECT 1 FROM conv c WHERE c.sale_case=s.sale_case AND c.series='A-1') THEN 1 ELSE 0 END AS a1_conv
    FROM sale_cases s
), leg AS (
  SELECT st.*, MIN(st.proceeds, st.rank1_rem) AS rank1_paid,
         MAX(st.proceeds - MIN(st.proceeds, st.rank1_rem), 0) AS after_r1
    FROM state st
), leg2 AS (
  SELECT l.*, CASE WHEN l.a1_conv=0 THEN MIN(l.after_r1, p.a1_pref) ELSE 0 END AS a1_rank2_paid
    FROM leg l CROSS JOIN params p
), numeric AS (
  SELECT l.*, l.after_r1 - l.a1_rank2_paid AS common_resid,
         p.common_sh + l.conv_sh AS common_pool
    FROM leg2 l CROSS JOIN params p
), combined AS (
  SELECT n.sale_case, p.series AS security,
         CASE WHEN c.series IS NOT NULL THEN n.common_resid * p.shares / n.common_pool
              WHEN p.series='A-1' THEN n.a1_rank2_paid
              WHEN p.rank=1 THEN n.rank1_paid * p.pref_m / n.rank1_rem
              ELSE 0 END AS cash_m,
         p.shares AS orig_shares
    FROM numeric n CROSS JOIN pref p
    LEFT JOIN conv c ON c.sale_case=n.sale_case AND c.series=p.series
  UNION ALL
  SELECT n.sale_case, 'common_A', n.common_resid * x.common_a_sh / n.common_pool, x.common_a_sh
    FROM numeric n CROSS JOIN params x
  UNION ALL
  SELECT n.sale_case, 'common_B', n.common_resid * x.common_b_sh / n.common_pool, x.common_b_sh
    FROM numeric n CROSS JOIN params x
)
SELECT sale_case, security, cash_m AS cash_usd_million,
       cash_m * 1000000.0 / orig_shares AS payout_per_share
FROM combined
ORDER BY sale_case, security;
