WITH recast AS (
 SELECT c.*,c.operating+CASE WHEN p.basis='sale' THEN f.dpp_collections ELSE 0 END operating_cash,
 c.investing-CASE WHEN p.basis='sale' THEN f.dpp_collections-f.purchaser_payment ELSE 0 END investing_cash,
 c.financing-CASE WHEN p.basis='sale' THEN f.purchaser_payment ELSE 0 END financing_cash
 FROM cash_flows c JOIN facility_policy p USING(period)
 LEFT JOIN facility_flows f USING(period)
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
