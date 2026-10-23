WITH movements AS (
 SELECT f.period,f.receivables_sold-f.new_transfer_cash new_dpp_from_transfers,
 e.purchaser_funding-b.purchaser_funding funding_change,e.dpp-b.dpp reported_dpp_change,
 c.noncash_dpp-f.dpp_collections-(e.purchaser_funding-b.purchaser_funding) explained_dpp_change
 FROM cash_flows c JOIN facility_flows f USING(period)
 CROSS JOIN facility_balances b JOIN facility_balances e ON e.sequence=b.sequence+1
) SELECT *,reported_dpp_change-explained_dpp_change unallocated_dpp_change FROM movements
