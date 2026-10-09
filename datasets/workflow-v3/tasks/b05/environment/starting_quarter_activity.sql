SELECT period,active_accounts_million,transactions_million,
1.0*transactions_million/active_accounts_million quarter_transactions_per_active_account,reported_ttm_activity
FROM quarters WHERE period IN ('Q4FY2024','Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025')
