WITH components AS (SELECT measure,
MAX(CASE WHEN period='FY2024' THEN amount_usd_million END) p,
MAX(CASE WHEN period='FY2025' THEN amount_usd_million END) c FROM revenues
WHERE period IN ('FY2024','FY2025') AND measure IN ('consumer','institutional','other_transaction','stablecoin','blockchain_rewards','interest_finance','other_subscription','corporate_interest') GROUP BY measure),
totals AS (SELECT MAX(CASE WHEN period='FY2025' THEN amount_usd_million END)-MAX(CASE WHEN period='FY2024' THEN amount_usd_million END) delta
FROM revenues WHERE measure='total_revenue' AND period IN ('FY2024','FY2025'))
SELECT measure,p prior_usd_million,c current_usd_million,c-p change_usd_million,100.0*(c-p)/delta contribution_to_total_growth_pct FROM components CROSS JOIN totals
