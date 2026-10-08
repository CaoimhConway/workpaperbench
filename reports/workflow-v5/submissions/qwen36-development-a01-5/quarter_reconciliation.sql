WITH q1_2025 AS (
    SELECT
        (SELECT amount FROM financials WHERE period_end = '2024-12-31' AND months = 6 AND measure = 'Total revenue') - (SELECT amount FROM financials WHERE period_end = '2024-12-31' AND months = 3 AND measure = 'Total revenue') AS revenue,
        (SELECT amount FROM financials WHERE period_end = '2024-12-31' AND months = 6 AND measure = 'Operating income') - (SELECT amount FROM financials WHERE period_end = '2024-12-31' AND months = 3 AND measure = 'Operating income') AS operating_income
),
q2_2025 AS (
    SELECT
        (SELECT amount FROM financials WHERE period_end = '2024-12-31' AND months = 3 AND measure = 'Total revenue') AS revenue,
        (SELECT amount FROM financials WHERE period_end = '2024-12-31' AND months = 3 AND measure = 'Operating income') AS operating_income
),
q1_2024 AS (
    SELECT
        (SELECT amount FROM financials WHERE period_end = '2023-12-31' AND months = 6 AND measure = 'Total revenue') - (SELECT amount FROM financials WHERE period_end = '2023-12-31' AND months = 3 AND measure = 'Total revenue') AS revenue,
        (SELECT amount FROM financials WHERE period_end = '2023-12-31' AND months = 6 AND measure = 'Operating income') - (SELECT amount FROM financials WHERE period_end = '2023-12-31' AND months = 3 AND measure = 'Operating income') AS operating_income
),
q2_2024 AS (
    SELECT
        (SELECT amount FROM financials WHERE period_end = '2023-12-31' AND months = 3 AND measure = 'Total revenue') AS revenue,
        (SELECT amount FROM financials WHERE period_end = '2023-12-31' AND months = 3 AND measure = 'Operating income') AS operating_income
),
margins AS (
    SELECT 2025 AS fiscal_year,
           ROUND((q2.operating_income * 100.0 / q2.revenue) - (q1.operating_income * 100.0 / q1.revenue), 6) AS margin_diff_pct
    FROM q1_2025 q1 CROSS JOIN q2_2025 q2
    UNION ALL
    SELECT 2024,
           ROUND((q2.operating_income * 100.0 / q2.revenue) - (q1.operating_income * 100.0 / q1.revenue), 6) AS margin_diff_pct
    FROM q1_2024 q1 CROSS JOIN q2_2024 q2
)
SELECT fiscal_year, ROUND(margin_diff_pct * 10000.0, 6) AS margin_qoq_bps FROM margins;
