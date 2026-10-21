SELECT CAST(s.year AS INTEGER) year,s.mrr_usd_million,12.0*s.mrr_usd_million exit_annual_run_rate_usd_million,
p.subscription_revenue_usd_million observed_annual_subscription_revenue_usd_million,
12.0*s.mrr_usd_million-p.subscription_revenue_usd_million run_rate_minus_observed_usd_million,
100.0*(12.0*s.mrr_usd_million/p.subscription_revenue_usd_million-1) run_rate_gap_pct
FROM subscription_stocks s JOIN periods p ON s.year=p.year AND p.months=12 WHERE s.year IN (2024,2025)
