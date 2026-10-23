WITH pref AS (
  SELECT t.series, p.shares, t.rank, t.forced_eligible,
         t.issue_price * t.preference_multiple * p.shares / 1000000.0 AS pref_m
  FROM terms t JOIN preferred p ON p.series = t.series
),
p AS (
  SELECT
    (SELECT SUM(pref_m) FROM pref WHERE rank = 1) AS rtot,
    (SELECT SUM(pref_m) FROM pref WHERE rank = 1 AND series <> 'A') AS r0,
    (SELECT SUM(shares) FROM common) + (SELECT COALESCE(SUM(shares), 0) FROM pref WHERE forced_eligible = 1) AS forced_sh,
    (SELECT SUM(shares) FROM common) AS common_sh,
    (SELECT shares FROM common WHERE security='common_A') AS common_a_sh,
    (SELECT shares FROM common WHERE security='common_B') AS common_b_sh,
    (SELECT shares FROM pref WHERE series='A') AS a_sh,
    (SELECT pref_m FROM pref WHERE series='A') AS a_pref,
    (SELECT pref_m FROM pref WHERE series='B') AS b_pref,
    (SELECT pref_m FROM pref WHERE series='C') AS c_pref,
    (SELECT pref_m FROM pref WHERE series='D') AS d_pref,
    (SELECT pref_m FROM pref WHERE series='D-1') AS d1_pref,
    (SELECT pref_m FROM pref WHERE series='F') AS f_pref,
    (SELECT shares FROM pref WHERE series='B') AS b_sh,
    (SELECT shares FROM pref WHERE series='C') AS c_sh,
    (SELECT shares FROM pref WHERE series='D') AS d_sh,
    (SELECT shares FROM pref WHERE series='D-1') AS d1_sh
)
SELECT t.target_case,
       CASE
         WHEN t.security='A' AND t.cash_target*p.rtot/p.a_pref <= 240 THEN t.cash_target*p.rtot/p.a_pref
         WHEN t.security='A' THEN p.r0 + t.cash_target*p.forced_sh/p.a_sh
         WHEN t.security='F' AND t.cash_target*p.rtot/p.f_pref <= 240 THEN t.cash_target*p.rtot/p.f_pref
         WHEN t.security='F' AND t.cash_target <= 240*p.f_pref/p.r0 THEN 240
         WHEN t.security='common_A' THEN (p.r0-p.b_pref) + t.cash_target*(p.forced_sh+p.b_sh)/p.common_a_sh
         WHEN t.security='common_B' THEN (p.r0-p.b_pref-p.c_pref-p.d_pref-p.d1_pref)
              + t.cash_target*(p.forced_sh+p.b_sh+p.c_sh+p.d_sh+p.d1_sh)/p.common_b_sh
       END AS proceeds_infimum_usd_million,
       CASE
         WHEN t.security='F' AND t.cash_target*p.rtot/p.f_pref > 240
              AND t.cash_target <= 240*p.f_pref/p.r0 THEN 0
         ELSE 1
       END AS attained
FROM owner_targets t CROSS JOIN p
ORDER BY t.target_case;
