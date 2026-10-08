WITH periods AS (
 SELECT period_end, MAX(CASE WHEN months=3 AND measure='Total revenue' THEN amount END) r2,
 MAX(CASE WHEN months=6 AND measure='Total revenue' THEN amount END) rh,
 MAX(CASE WHEN months=3 AND measure='Operating income' THEN amount END) o2,
 MAX(CASE WHEN months=6 AND measure='Operating income' THEN amount END) oh
 FROM financials WHERE period_end IN ('2023-12-31','2024-12-31') GROUP BY period_end
), quarters AS (
 SELECT CAST(substr(period_end,1,4) AS INTEGER)+1 fiscal_year,1 quarter,rh-r2 revenue,oh-o2 income FROM periods
 UNION ALL SELECT CAST(substr(period_end,1,4) AS INTEGER)+1,2,r2,o2 FROM periods
) SELECT fiscal_year,quarter,revenue revenue_usd_million,income operating_income_usd_million,
100.0*income/revenue operating_margin_pct FROM quarters
