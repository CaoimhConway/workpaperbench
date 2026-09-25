SELECT 'FY2025' period,i.membership_usd_million earned_fees_usd_million,p.amount_usd_million opening_deferred_usd_million,
c.amount_usd_million closing_deferred_usd_million,c.amount_usd_million-p.amount_usd_million deferred_change_usd_million,
i.membership_usd_million+c.amount_usd_million-p.amount_usd_million mechanical_accrual_bridge_usd_million
FROM income i JOIN deferred_membership p ON p.economic_date='2024-09-01' JOIN deferred_membership c ON c.economic_date='2025-08-31'
WHERE i.fiscal_year=2025 AND i.weeks=52
