WITH q2_2025 AS (
    SELECT
        (SELECT amount FROM financials WHERE period_end = '2024-12-31' AND months = 3 AND measure = 'Total revenue') AS revenue,
        (SELECT amount FROM financials WHERE period_end = '2024-12-31' AND months = 3 AND measure = 'Operating income') AS operating_income
),
q1_2025 AS (
    SELECT
        (SELECT amount FROM financials WHERE period_end = '2024-12-31' AND months = 6 AND measure = 'Total revenue') - q2.revenue AS revenue,
        (SELECT amount FROM financials WHERE period_end = '2024-12-31' AND months = 6 AND measure = 'Operating income') - q2.operating_income AS operating_income
    FROM q2_2025 q2
),
q2_2024 AS (
    SELECT
        (SELECT amount FROM financials WHERE period_end = '2023-12-31' AND months = 3 AND measure = 'Total revenue') AS revenue,
        (SELECT amount FROM financials WHERE period_end = '2023-12-31' AND months = 3 AND measure = 'Operating income') AS operating_income
),
q1_2024 AS (
    SELECT
        (SELECT amount FROM financials WHERE period_end = '2023-12-31' AND months = 6 AND measure = 'Total revenue') - q2.revenue AS revenue,
        (SELECT amount FROM financials WHERE period_end = '2023-12-31' AND months = 6 AND measure = 'Operating income') - q2.operating_income AS operating_income
    FROM q2_2024 q2
)
SELECT 2025 AS fiscal_year, 1 AS quarter, revenue AS revenue_usd_million, operating_income AS operating_income_usd_million, ROUND(operating_income * 100.0 / revenue, 6) AS operating_margin_pct FROM q1_2025
UNION ALL
SELECT 2025, 2, revenue, operating_income, ROUND(operating_income * 100.0 / revenue, 6) FROM q2_2025
UNION ALL
SELECT 2024, 1, revenue, operating_income, ROUND(operating_income * 100.0 / revenue, 6) FROM q1_2024
UNION ALL
SELECT 2024, 2, revenue, operating_income, ROUND(operating_income * 100.0 / revenue, 6) FROM q2_2024;
