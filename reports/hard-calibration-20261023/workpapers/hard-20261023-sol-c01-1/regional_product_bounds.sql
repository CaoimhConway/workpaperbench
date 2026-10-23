WITH
regions AS (
    SELECT geography, net_sales
    FROM geographies
    WHERE geography IN ('us', 'china', 'other')
),
products AS (
    SELECT net_sales AS product_sales
    FROM business_lines
    WHERE business_line = 'products'
),
region_total AS (
    SELECT SUM(net_sales) AS total_sales FROM regions
)
SELECT
    geography,
    MAX(0.0, product_sales - (total_sales - net_sales)) AS lower_usd_million,
    MIN(product_sales, net_sales) AS upper_usd_million
FROM regions CROSS JOIN products CROSS JOIN region_total;
