WITH current_period AS (
    SELECT revenue, pretax, contingent_fv_expense
    FROM periods
    WHERE year = 2020
), prior_actual AS (
    SELECT revenue FROM periods WHERE year = 2019
), prior_proforma AS (
    SELECT revenue FROM proforma_revenue WHERE year = 2019
), immediate_expenses AS (
    SELECT SUM(iprd_charge + sales_admin_award_charge + research_award_charge)
               AS amount
    FROM acquisition_effects
    WHERE deal = 'MyoKardia' AND year = 2020
)
SELECT 'reported_revenue_growth_percent' AS measure,
       100.0 * (c.revenue - p.revenue) / p.revenue AS value
FROM current_period AS c CROSS JOIN prior_actual AS p
UNION ALL
SELECT 'proforma_baseline_revenue_growth_percent',
       100.0 * (c.revenue - p.revenue) / p.revenue
FROM current_period AS c CROSS JOIN prior_proforma AS p
UNION ALL
SELECT 'immediate_myokardia_expenses_usd_million', amount
FROM immediate_expenses
UNION ALL
SELECT 'selected_effects_excluded_pretax_usd_million',
       c.pretax + e.amount + c.contingent_fv_expense
FROM current_period AS c CROSS JOIN immediate_expenses AS e;
