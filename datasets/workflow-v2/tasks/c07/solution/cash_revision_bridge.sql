SELECT a.measure,r.amount_usd_million prior_release_usd_million,a.amount_usd_million annual_report_usd_million,
a.amount_usd_million-r.amount_usd_million change_usd_million FROM cash_versions a JOIN cash_versions r
ON a.measure=r.measure AND a.year=r.year AND a.version='annual' AND r.version='release' WHERE a.year=2025
