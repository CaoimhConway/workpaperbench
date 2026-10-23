SELECT
  'reported_revenue_growth_percent' AS measure,
  ((SELECT revenue FROM periods WHERE year = 2020) / (SELECT revenue FROM periods WHERE year = 2019) - 1.0) * 100.0 AS value
UNION ALL
SELECT
  'proforma_baseline_revenue_growth_percent',
  ((SELECT revenue FROM periods WHERE year = 2020) / (SELECT revenue FROM proforma_revenue WHERE year = 2019) - 1.0) * 100.0
UNION ALL
SELECT
  'immediate_myokardia_expenses_usd_million',
  (SELECT SUM(iprd_charge + sales_admin_award_charge + research_award_charge)
   FROM acquisition_effects
   WHERE deal = 'MyoKardia' AND year = 2020)
UNION ALL
SELECT
  'selected_effects_excluded_pretax_usd_million',
  (SELECT p.pretax + e.myokardia_expenses + p.contingent_fv_expense
   FROM periods p
   JOIN (SELECT SUM(iprd_charge + sales_admin_award_charge + research_award_charge) AS myokardia_expenses
         FROM acquisition_effects
         WHERE deal = 'MyoKardia' AND year = 2020) e
   WHERE p.year = 2020);
