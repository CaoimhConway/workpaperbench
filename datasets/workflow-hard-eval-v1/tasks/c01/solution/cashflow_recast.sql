WITH recast AS (
 SELECT c.*,c.operating+CASE WHEN p.basis='sale' THEN f.dpp_collections ELSE 0 END operating_cash,
 c.investing-CASE WHEN p.basis='sale' THEN f.dpp_collections-f.purchaser_payment ELSE 0 END investing_cash,
 c.financing-CASE WHEN p.basis='sale' THEN f.purchaser_payment ELSE 0 END financing_cash
 FROM cash_flows c JOIN facility_policy p USING(period)
 LEFT JOIN facility_flows f USING(period)
) SELECT period,operating_cash,investing_cash,financing_cash,
 operating_cash+investing_cash+financing_cash total_cash FROM recast
