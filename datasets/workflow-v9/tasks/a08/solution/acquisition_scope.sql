SELECT c.months,c.subscription_usd_million+c.professional_usd_million current_revenue_usd_million,
p.subscription_usd_million+p.professional_usd_million prior_revenue_usd_million,a.total_revenue_usd_million acquired_revenue_usd_million,
c.subscription_usd_million+c.professional_usd_million-a.total_revenue_usd_million current_ex_disclosed_acquisition_usd_million,
100.0*((c.subscription_usd_million+c.professional_usd_million)/(p.subscription_usd_million+p.professional_usd_million)-1) reported_growth_pct,
100.0*((c.subscription_usd_million+c.professional_usd_million-a.total_revenue_usd_million)/(p.subscription_usd_million+p.professional_usd_million)-1) arithmetic_ex_acquisition_growth_pct,
c.subscription_usd_million-a.subscription_usd_million subscription_ex_acquisition_usd_million FROM income c JOIN income p ON c.months=p.months AND c.fiscal_year=2026 AND p.fiscal_year=2025
JOIN acquired_revenue a ON a.fiscal_year=c.fiscal_year AND a.months=c.months WHERE c.months IN (3,12)
