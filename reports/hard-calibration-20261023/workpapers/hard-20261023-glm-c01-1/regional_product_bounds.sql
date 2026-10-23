WITH products_total AS (
    SELECT
        MAX(CASE WHEN business_line = 'products' THEN net_sales END) AS products_sales
    FROM business_lines
),
geography AS (
    SELECT
        g.geography,
        g.net_sales AS geography_sales,
        COALESCE((
            SELECT SUM(o.net_sales)
            FROM geographies o
            WHERE o.geography <> g.geography
        ), 0.0) AS other_geography_sales
    FROM geographies g
)
SELECT
    geography,
    CASE
        WHEN p.products_sales - g.other_geography_sales > 0.0
        THEN p.products_sales - g.other_geography_sales
        ELSE 0.0
    END AS lower_usd_million,
    CASE
        WHEN g.geography_sales < p.products_sales
        THEN g.geography_sales
        ELSE p.products_sales
    END AS upper_usd_million
FROM geography g
CROSS JOIN products_total p;
