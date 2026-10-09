SELECT CAST(c.months AS INTEGER) months,p.net_income_usd_million prior_gaap_usd_million,a.tax_charge_usd_million,
p.net_income_usd_million-a.tax_charge_usd_million prior_adjusted_usd_million,c.net_income_usd_million current_gaap_usd_million,
100.0*(c.net_income_usd_million/p.net_income_usd_million-1) gaap_growth_pct,
100.0*(c.net_income_usd_million/(p.net_income_usd_million-a.tax_charge_usd_million)-1) current_gaap_growth_vs_adjusted_prior_pct,
p.net_income_usd_million-a.tax_charge_usd_million-a.reported_adjusted_net_income_usd_million residual_usd_million
FROM income c JOIN income p ON c.months=p.months AND c.year=2025 AND p.year=2024
JOIN prior_tax_adjustments a ON a.year=p.year AND a.months=p.months
