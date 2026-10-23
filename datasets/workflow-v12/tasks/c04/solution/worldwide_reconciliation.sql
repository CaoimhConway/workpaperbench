WITH p AS (SELECT period,SUM(gdv_usd_billion) g,SUM(purchase_usd_billion) v,SUM(purchase_transactions_million) n
FROM regions WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025') GROUP BY period)
SELECT p.period,g regional_gdv_usd_billion,v regional_purchase_usd_billion,n regional_purchase_transactions_million,
g-w.gdv_usd_billion gdv_residual_usd_billion,v-w.purchase_usd_billion purchase_residual_usd_billion,
n-w.purchase_transactions_million transaction_residual_million FROM p JOIN worldwide w USING(period)
