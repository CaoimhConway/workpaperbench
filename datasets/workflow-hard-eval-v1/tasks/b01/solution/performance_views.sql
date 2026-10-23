WITH current AS (SELECT * FROM periods WHERE year=2020),
 prior AS (SELECT * FROM periods WHERE year=2019),
 comparable AS (SELECT * FROM proforma_revenue WHERE year=2019),
 charges AS (SELECT iprd_charge+sales_admin_award_charge+research_award_charge amount
 FROM acquisition_effects WHERE deal='MyoKardia')
 SELECT 'reported_revenue_growth_percent' measure,(c.revenue/p.revenue-1)*100 value FROM current c CROSS JOIN prior p
 UNION ALL SELECT 'proforma_baseline_revenue_growth_percent',(c.revenue/p.revenue-1)*100 FROM current c CROSS JOIN comparable p
 UNION ALL SELECT 'immediate_myokardia_expenses_usd_million',amount FROM charges
 UNION ALL SELECT 'selected_effects_excluded_pretax_usd_million',pretax+amount+contingent_fv_expense
 FROM current CROSS JOIN charges
