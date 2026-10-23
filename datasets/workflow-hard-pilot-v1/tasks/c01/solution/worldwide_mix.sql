SELECT business_line,net_sales net_sales_usd_million,net_sales-cost_of_sales gross_profit_usd_million,
 100.0*(net_sales-cost_of_sales)/net_sales gross_margin_pct FROM business_lines
