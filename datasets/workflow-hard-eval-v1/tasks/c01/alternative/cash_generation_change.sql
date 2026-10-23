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
) , changes AS (
 SELECT n.operating-o.operating reported_operating_change,
 n.operating_cash-o.operating_cash normalized_operating_change,
 n.collateral-o.collateral collateral_change,n.capex-o.capex capex_change
 FROM recast o JOIN recast n ON n.sequence=o.sequence+1
) SELECT reported_operating_change,normalized_operating_change,
 reported_operating_change-normalized_operating_change presentation_effect,
 collateral_change,normalized_operating_change-collateral_change other_operating_change,
 normalized_operating_change-capex_change normalized_after_capex_change,
 normalized_operating_change-collateral_change-capex_change other_after_capex_change
 FROM changes
