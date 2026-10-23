-- Write each loss as an all-Services baseline plus the incremental loss
-- from assigning Products sales to a region. With only one allocation sum
-- and regional capacity bounds, filling capacities in coefficient order
-- attains the minimum; reversing the order attains the maximum.
WITH
worldwide AS (
    SELECT
        SUM(CASE WHEN business_line = 'products' THEN net_sales ELSE 0 END) AS product_sales,
        SUM(net_sales) AS revenue,
        SUM(net_sales - cost_of_sales) AS gross_profit,
        MAX(CASE WHEN business_line = 'products'
            THEN 1.0 * (net_sales - cost_of_sales) / net_sales END) AS product_margin,
        MAX(CASE WHEN business_line = 'services'
            THEN 1.0 * (net_sales - cost_of_sales) / net_sales END) AS service_margin
    FROM business_lines
    WHERE business_line IN ('products', 'services')
),
measures AS (
    SELECT 'revenue' AS measure, revenue AS denominator,
        1.0 AS product_factor, 1.0 AS service_factor, product_sales
    FROM worldwide
    UNION ALL
    SELECT 'gross_profit', gross_profit, product_margin, service_margin, product_sales
    FROM worldwide
),
coefficients AS (
    SELECT m.measure, m.denominator, m.product_sales,
        g.geography, g.net_sales AS capacity,
        g.net_sales * r.services_loss_pct / 100.0 * m.service_factor AS baseline,
        (r.products_loss_pct * m.product_factor
          - r.services_loss_pct * m.service_factor) / 100.0 AS coefficient
    FROM measures AS m
    CROSS JOIN geographies AS g
    JOIN stress_rates AS r ON r.geography = g.geography
    WHERE g.geography IN ('us', 'china', 'other')
),
ranked AS (
    SELECT *,
        COALESCE(SUM(capacity) OVER (
            PARTITION BY measure ORDER BY coefficient, geography
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0.0) AS capacity_before_min,
        COALESCE(SUM(capacity) OVER (
            PARTITION BY measure ORDER BY coefficient DESC, geography
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0.0) AS capacity_before_max
    FROM coefficients
),
losses AS (
    SELECT measure, denominator,
        SUM(baseline + coefficient * MIN(capacity,
            MAX(0.0, product_sales - capacity_before_min))) AS lower_loss,
        SUM(baseline + coefficient * MIN(capacity,
            MAX(0.0, product_sales - capacity_before_max))) AS upper_loss
    FROM ranked
    GROUP BY measure, denominator
)
SELECT measure,
    lower_loss AS lower_usd_million,
    upper_loss AS upper_usd_million,
    100.0 * lower_loss / denominator AS lower_pct,
    100.0 * upper_loss / denominator AS upper_pct
FROM losses;
