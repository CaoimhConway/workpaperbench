SELECT "fiscal_year", "margin_qoq_bps" FROM (
WITH p AS (
 SELECT period_end,MAX(CASE WHEN months=3 AND measure='Total revenue' THEN amount END) r2,
 MAX(CASE WHEN months=6 AND measure='Total revenue' THEN amount END) rh,
 MAX(CASE WHEN months=3 AND measure='Operating income' THEN amount END) o2,
 MAX(CASE WHEN months=6 AND measure='Operating income' THEN amount END) oh
 FROM financials WHERE period_end IN ('2023-12-31','2024-12-31') GROUP BY period_end
) SELECT CAST(substr(period_end,1,4) AS INTEGER)+1 fiscal_year,
(rh-r2)+r2-rh revenue_residual_usd_million,(oh-o2)+o2-oh operating_income_residual_usd_million,
10000.0*(o2/r2-(oh-o2)/(rh-r2)) margin_qoq_bps FROM p
) AS workpaper
