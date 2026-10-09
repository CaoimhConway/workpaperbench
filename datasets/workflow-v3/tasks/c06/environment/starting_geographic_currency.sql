SELECT comparison,region,prior_usd_million,current_usd_million,fx_effect_usd_million,current_usd_million-fx_effect_usd_million cc_current_usd_million,
100.0*(current_usd_million/prior_usd_million-1) reported_growth_pct,
100.0*((current_usd_million-fx_effect_usd_million)/prior_usd_million-1) cc_growth_pct FROM geography WHERE comparison IN ('year_over_year','quarter_over_quarter')
