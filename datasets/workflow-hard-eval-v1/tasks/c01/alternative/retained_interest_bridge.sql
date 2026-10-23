WITH pool AS (
 SELECT f.period,f.receivables_sold-f.new_transfer_cash new_dpp_from_transfers,
 e.purchaser_funding-b.purchaser_funding funding_change,
 (e.pool_fair_value-e.purchaser_funding)-(b.pool_fair_value-b.purchaser_funding) reported_dpp_change,
 f.receivables_sold-f.cash_reinvested-(e.purchaser_funding-b.purchaser_funding) explained_dpp_change
 FROM facility_flows f CROSS JOIN facility_balances b
 JOIN facility_balances e ON e.sequence=b.sequence+1
) SELECT *,reported_dpp_change-explained_dpp_change unallocated_dpp_change FROM pool
