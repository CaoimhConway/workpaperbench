# Source dossier

2024 Form 10-K

https://d18rn0p25nwr6d.cloudfront.net/CIK-0000320193/1e7e3da9-526f-477e-add2-b6ea6deb3d81.html

Published 2024-11-01. Whole USD million. Bounds concern all nonnegative joint allocations consistent with these displayed annual marginals. No estimate of the actual undisclosed mix is substituted.

## c01:s01

p. 29, Consolidated Statements of Operations, FY2024 Products and Services net sales and cost of sales

Selected factual table columns are normalized below.

## c01:s02

p. 47, Note 13, net sales by country, FY2024

China includes Hong Kong and Taiwan. U.S. is a country disclosure, not the Americas operating segment. The supplied country totals and Products/Services totals do not disclose their joint allocation.

## c01:s03

p. 21, fiscal period definition

FY2024 spans 52 weeks and ends September 28, 2024. These are annual net sales, not balances, customer counts or cash receipts.

## c01:s04

Authored stress scenario, not an issuer observation

Authored sensitivity scenario, not an issuer forecast: allocate sales into nonnegative Products/Services by U.S., China (including Hong Kong and Taiwan), and other countries, preserving both sets of supplied totals. No other cross-cell constraints apply. The rates in stress_rates are percentage reductions of the relevant cell sales. Lost sales carry that business line's worldwide FY2024 gross margin in every geography. Beyond the cost-of-sales change implied by those margins, no secondary demand response, geographic switching or other profit changes occur. Gross profit here is sales less cost of sales. Optimize revenue and gross-profit loss separately over the same feasible allocations. Bounds are inclusive. The actual joint allocation is unknown.

## Normalized input tables

These retain source observations. stress_rates, where present, contains authored scenario assumptions. Full source documents are not redistributed.

### business_lines

```json
[
  {
    "business_line": "products",
    "net_sales": 294866,
    "cost_of_sales": 185233
  },
  {
    "business_line": "services",
    "net_sales": 96169,
    "cost_of_sales": 25119
  }
]
```

### geographies

```json
[
  {
    "geography": "us",
    "net_sales": 142196
  },
  {
    "geography": "china",
    "net_sales": 66952
  },
  {
    "geography": "other",
    "net_sales": 181887
  }
]
```

### stress_rates

```json
[
  {
    "geography": "us",
    "products_loss_pct": 5,
    "services_loss_pct": 2
  },
  {
    "geography": "china",
    "products_loss_pct": 25,
    "services_loss_pct": 10
  },
  {
    "geography": "other",
    "products_loss_pct": 12,
    "services_loss_pct": 3
  }
]
```

Attributed factual observations and concise definitions only. Issuer material is excluded from the project MIT license. Full source documents are not redistributed.
