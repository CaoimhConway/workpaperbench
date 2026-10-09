WITH g AS (SELECT comparison,SUM(prior_usd_million) p,SUM(current_usd_million) c,SUM(fx_effect_usd_million) f FROM geography GROUP BY comparison)
SELECT g.comparison,p+h.prior_usd_million prior_reported_usd_million,c+h.current_usd_million current_reported_usd_million,
c-f cc_current_usd_million,c-f-p cc_change_usd_million,f fx_effect_usd_million,h.current_usd_million-h.prior_usd_million hedging_change_usd_million,
c+h.current_usd_million-p-h.prior_usd_million reported_change_usd_million,
(c-f-p)+f+(h.current_usd_million-h.prior_usd_million)-(c+h.current_usd_million-p-h.prior_usd_million) bridge_residual_usd_million,
100.0*((c-f)/p-1) cc_growth_pct,c-f-h.reported_cc_usd_million cc_disclosure_residual_usd_million FROM g JOIN hedging h ON g.comparison=h.comparison
WHERE g.comparison IN ('year_over_year','quarter_over_quarter')
