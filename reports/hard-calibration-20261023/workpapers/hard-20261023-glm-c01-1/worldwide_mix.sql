WITH annual AS (
    SELECT
        business_line,
        net_sales,
        cost_of_sales
    FROM business_lines
    WHERE business_line IN ('products', 'services')
)
SELECT
    business_line,
    net_sales AS net_sales_usd_million,
    net_sales - cost_of_sales AS gross_profit_usd_million,
    100.0 * (net_sales - cost_of_sales) / net_sales AS gross_margin_pct
FROM annual;
