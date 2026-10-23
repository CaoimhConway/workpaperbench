WITH myokardia_effects AS (
    SELECT
        year,
        SUM(iprd_charge
            + sales_admin_award_charge
            + research_award_charge) AS immediate_expenses
    FROM acquisition_effects
    WHERE deal = 'MyoKardia'
    GROUP BY year
),
measure_inputs AS (
    SELECT
        (SELECT revenue FROM periods WHERE year = 2020)
            AS revenue_2020,
        (SELECT revenue FROM periods WHERE year = 2019)
            AS revenue_2019_actual,
        (SELECT revenue FROM proforma_revenue WHERE year = 2019)
            AS revenue_2019_proforma,
        (SELECT pretax FROM periods WHERE year = 2020)
            AS pretax_2020,
        (SELECT contingent_fv_expense FROM periods WHERE year = 2020)
            AS contingent_fv_expense_2020,
        (SELECT immediate_expenses FROM myokardia_effects WHERE year = 2020)
            AS immediate_myokardia_expenses
)
SELECT
    'reported_revenue_growth_percent' AS measure,
    (revenue_2020 * 1.0 / revenue_2019_actual - 1.0) * 100.0 AS value
FROM measure_inputs
UNION ALL
SELECT
    'proforma_baseline_revenue_growth_percent',
    (revenue_2020 * 1.0 / revenue_2019_proforma - 1.0) * 100.0
FROM measure_inputs
UNION ALL
SELECT
    'immediate_myokardia_expenses_usd_million',
    immediate_myokardia_expenses
FROM measure_inputs
UNION ALL
SELECT
    'selected_effects_excluded_pretax_usd_million',
    pretax_2020
        + contingent_fv_expense_2020
        + immediate_myokardia_expenses
FROM measure_inputs;
