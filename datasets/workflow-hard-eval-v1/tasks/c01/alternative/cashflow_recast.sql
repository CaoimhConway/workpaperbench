WITH journal AS (
 SELECT period,'operating' category,operating amount FROM cash_flows
 UNION ALL SELECT period,'investing',investing FROM cash_flows
 UNION ALL SELECT period,'financing',financing FROM cash_flows
 UNION ALL SELECT f.period,'operating',f.dpp_collections FROM facility_flows f
 JOIN facility_policy p USING(period) WHERE p.basis='sale'
 UNION ALL SELECT f.period,'investing',-f.dpp_collections FROM facility_flows f
 JOIN facility_policy p USING(period) WHERE p.basis='sale'
 UNION ALL SELECT f.period,'investing',f.purchaser_payment FROM facility_flows f
 JOIN facility_policy p USING(period) WHERE p.basis='sale'
 UNION ALL SELECT f.period,'financing',-f.purchaser_payment FROM facility_flows f
 JOIN facility_policy p USING(period) WHERE p.basis='sale'
), recast AS (
 SELECT c.*,SUM(CASE WHEN category='operating' THEN amount ELSE 0 END) operating_cash,
 SUM(CASE WHEN category='investing' THEN amount ELSE 0 END) investing_cash,
 SUM(CASE WHEN category='financing' THEN amount ELSE 0 END) financing_cash
 FROM cash_flows c JOIN journal j USING(period) GROUP BY c.period
) SELECT period,operating_cash,investing_cash,financing_cash,
 operating_cash+investing_cash+financing_cash total_cash FROM recast
