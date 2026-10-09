WITH p AS (SELECT fiscal_year,CASE months WHEN 3 THEN 'Q2' ELSE 'H1' END window,revenue_usd_million revenue,
gaap_gross_profit_usd_million gaap,acquisition_adjustment_usd_million+stock_adjustment_usd_million+other_adjustment_usd_million adjustment,
reported_adjusted_gross_profit_usd_million reported,operating_cash_usd_million ocf,property_and_intangible_spending_usd_million purchase,
property_intangible_principal_usd_million principal,reported_fcf_usd_million fcf FROM financials WHERE fiscal_year IN (2025,2026) AND months IN (3,6)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,'Q1',a.revenue-q.revenue,a.gaap-q.gaap,a.adjustment-q.adjustment,
a.reported-q.reported,a.ocf-q.ocf,a.purchase-q.purchase,a.principal-q.principal,a.fcf-q.fcf FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.window='H1' AND q.window='Q2') SELECT fiscal_year,window,ocf operating_cash_usd_million,purchase property_intangible_spending_usd_million,
principal property_intangible_principal_usd_million,ocf-purchase-principal fcf_usd_million,ocf-purchase-principal-fcf residual_usd_million FROM periods
