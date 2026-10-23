WITH pref AS (
  SELECT t.series, t.issue_price, t.preference_multiple, p.shares,
         (t.issue_price * t.preference_multiple * p.shares) / 1000000.0 AS pref_m,
         t.issue_price * t.preference_multiple AS pps,
         t.rank, t.forced_eligible
  FROM terms t JOIN preferred p ON p.series=t.series
), opt AS (SELECT * FROM pref WHERE forced_eligible=0),
cs AS (SELECT SUM(shares) AS sh FROM common),
forced AS (SELECT COALESCE(SUM(shares),0) AS sh FROM pref WHERE forced_eligible=1)
SELECT o.series,
       (SELECT COALESCE(SUM(h.pref_m),0) FROM pref h
         WHERE h.rank=1 AND h.forced_eligible=0 AND h.issue_price > o.issue_price)
       + o.pps * ((SELECT sh FROM cs) + (SELECT sh FROM forced)
                  + (SELECT COALESCE(SUM(l.shares),0) FROM pref l
                      WHERE l.forced_eligible=0 AND l.issue_price <= o.issue_price)) / 1000000.0
         AS proceeds_usd_million,
       o.pps AS common_payout_per_share
FROM opt o ORDER BY o.series;
