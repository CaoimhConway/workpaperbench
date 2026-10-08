WITH a AS (SELECT * FROM significant_items WHERE period='FY2025'),d AS (SELECT * FROM annual_significant_details WHERE period='FY2025')
SELECT 'apple_reserve' measure,apple_aftertax_effect_usd_million signed_aftertax_exclusion_usd_million,'printed_after_tax' origin FROM a
UNION ALL SELECT 'first_republic_gain',-(apple_aftertax_effect_usd_million-d.corporate_tax_benefit_usd_million-net_income_exclusion_change_usd_million),'derived_after_tax' FROM a CROSS JOIN d
UNION ALL SELECT 'corporate_tax_benefit',-corporate_tax_benefit_usd_million,'printed_after_tax' FROM d
