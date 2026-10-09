WITH annual AS (SELECT SUM(transactions_million) t,SUM(transaction_revenue_usd_million) r,
SUM(ovas_usd_million) o,SUM(net_revenue_usd_million) n,SUM(tpv_usd_million) v FROM quarters
WHERE period IN ('Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025'))
SELECT 'FY2025' period,t transactions_million,1.0*q.transactions_million/q.active_accounts_million recomputed_ttm_activity,
1.0*t/q.active_accounts_million-q.reported_ttm_activity rounded_activity_residual,r transaction_revenue_usd_million,
o ovas_usd_million,n net_revenue_usd_million,r+o-n revenue_residual_usd_million,v tpv_usd_million,100.0*r/v transaction_revenue_to_tpv_pct
FROM annual JOIN quarters q ON q.period='Q4FY2025'
