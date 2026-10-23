WITH b AS (
 SELECT c.cash_ppe,a.*,1000.0*(p.capital_payables_billion-o.capital_payables_billion) pc,
 p.gross-o.gross dg,p.accumulated-o.accumulated da
 FROM cash_flows c JOIN annual_expenses a USING(year) JOIN ppe p USING(year) JOIN ppe o ON o.year=c.year-1)
 SELECT pc payables_change_usd_million,cash_ppe+pc purchase_proxy_usd_million,
 finance_rou_additions lease_additions_usd_million,1000.0*ppe_depreciation_billion depreciation_usd_million,
 dg-da net_change_usd_million,cash_ppe+pc+finance_rou_additions-1000.0*ppe_depreciation_billion explained_change_usd_million,
 (dg-cash_ppe-pc-finance_rou_additions)-(da-1000.0*ppe_depreciation_billion) residual_usd_million FROM b
