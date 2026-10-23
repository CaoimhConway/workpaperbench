WITH business AS (
    SELECT
        MAX(CASE WHEN business_line = 'products' THEN net_sales END) AS products_sales,
        MAX(CASE WHEN business_line = 'products' THEN cost_of_sales END) AS products_cost,
        MAX(CASE WHEN business_line = 'services' THEN net_sales END) AS services_sales,
        MAX(CASE WHEN business_line = 'services' THEN cost_of_sales END) AS services_cost
    FROM business_lines
),
derived AS (
    SELECT
        *,
        products_sales + services_sales AS worldwide_revenue,
        products_sales - products_cost + services_sales - services_cost AS worldwide_gross_profit,
        (products_sales - products_cost) / products_sales AS products_margin,
        (services_sales - services_cost) / services_sales AS services_margin
    FROM business
),
geography AS (
    SELECT
        g.geography,
        g.net_sales AS geography_sales,
        r.products_loss_pct / 100.0 AS products_loss_rate,
        r.services_loss_pct / 100.0 AS services_loss_rate
    FROM geographies g
    JOIN stress_rates r ON r.geography = g.geography
),
geography_total AS (
    SELECT SUM(geography_sales) AS geography_sales
    FROM geography
),
products_bounds AS (
    SELECT
        b.geography,
        b.geography_sales,
        d.products_sales,
        CASE
            WHEN d.products_sales - (t.geography_sales - b.geography_sales) > 0.0
            THEN d.products_sales - (t.geography_sales - b.geography_sales)
            ELSE 0.0
        END AS lower_product_sales,
        CASE
            WHEN b.geography_sales < d.products_sales
            THEN b.geography_sales
            ELSE d.products_sales
        END AS upper_product_sales
    FROM geography b
    CROSS JOIN derived d
    CROSS JOIN geography_total t
),
endpoints AS (
    SELECT geography, lower_product_sales AS product_sales
    FROM products_bounds
    UNION ALL
    SELECT geography, upper_product_sales AS product_sales
    FROM products_bounds
),
vertices AS (
    SELECT
        eu.product_sales AS us_products,
        ec.product_sales AS china_products,
        d.products_sales - eu.product_sales - ec.product_sales AS other_products
    FROM endpoints eu
    JOIN endpoints ec ON ec.geography = 'china'
    JOIN products_bounds ro ON ro.geography = 'other'
    CROSS JOIN derived d
    WHERE eu.geography = 'us'
      AND d.products_sales - eu.product_sales - ec.product_sales
         BETWEEN ro.lower_product_sales AND ro.upper_product_sales

    UNION ALL

    SELECT
        eu.product_sales AS us_products,
        d.products_sales - eu.product_sales - eo.product_sales AS china_products,
        eo.product_sales AS other_products
    FROM endpoints eu
    JOIN endpoints eo ON eo.geography = 'other'
    JOIN products_bounds rc ON rc.geography = 'china'
    CROSS JOIN derived d
    WHERE eu.geography = 'us'
      AND d.products_sales - eu.product_sales - eo.product_sales
         BETWEEN rc.lower_product_sales AND rc.upper_product_sales

    UNION ALL

    SELECT
        d.products_sales - ec.product_sales - eo.product_sales AS us_products,
        ec.product_sales AS china_products,
        eo.product_sales AS other_products
    FROM endpoints ec
    JOIN endpoints eo ON eo.geography = 'other'
    JOIN products_bounds ru ON ru.geography = 'us'
    CROSS JOIN derived d
    WHERE ec.geography = 'china'
      AND d.products_sales - ec.product_sales - eo.product_sales
         BETWEEN ru.lower_product_sales AND ru.upper_product_sales
),
losses AS (
    SELECT
        gu.products_loss_rate * v.us_products
            + gu.services_loss_rate * (gu.geography_sales - v.us_products)
            + gc.products_loss_rate * v.china_products
            + gc.services_loss_rate * (gc.geography_sales - v.china_products)
            + go.products_loss_rate * v.other_products
            + go.services_loss_rate * (go.geography_sales - v.other_products) AS revenue_loss,
        d.products_margin * (
            gu.products_loss_rate * v.us_products
            + gc.products_loss_rate * v.china_products
            + go.products_loss_rate * v.other_products
        ) + d.services_margin * (
            gu.services_loss_rate * (gu.geography_sales - v.us_products)
            + gc.services_loss_rate * (gc.geography_sales - v.china_products)
            + go.services_loss_rate * (go.geography_sales - v.other_products)
        ) AS gross_profit_loss
    FROM vertices v
    JOIN geography gu ON gu.geography = 'us'
    JOIN geography gc ON gc.geography = 'china'
    JOIN geography go ON go.geography = 'other'
    CROSS JOIN derived d
)
SELECT
    'revenue' AS measure,
    MIN(revenue_loss) AS lower_usd_million,
    MAX(revenue_loss) AS upper_usd_million,
    100.0 * MIN(revenue_loss) / (SELECT worldwide_revenue FROM derived) AS lower_pct,
    100.0 * MAX(revenue_loss) / (SELECT worldwide_revenue FROM derived) AS upper_pct
FROM losses
UNION ALL
SELECT
    'gross_profit' AS measure,
    MIN(gross_profit_loss) AS lower_usd_million,
    MAX(gross_profit_loss) AS upper_usd_million,
    100.0 * MIN(gross_profit_loss) / (SELECT worldwide_gross_profit FROM derived) AS lower_pct,
    100.0 * MAX(gross_profit_loss) / (SELECT worldwide_gross_profit FROM derived) AS upper_pct
FROM losses;
