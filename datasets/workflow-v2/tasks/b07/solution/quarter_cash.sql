SELECT CAST(year AS INTEGER) year,CAST(quarter AS INTEGER) quarter,operating_cash_usd_million-capex_usd_million fcf_usd_million,
100.0*(operating_cash_usd_million-capex_usd_million)/revenue_usd_million fcf_margin_pct,
100.0*adjusted_ebitda_usd_million/revenue_usd_million adjusted_ebitda_margin_pct FROM quarters WHERE year IN (2024,2025)
