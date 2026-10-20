# Cisco FY2025 publication reconciliation

Fiscal years end July 26, 2025 and July 27, 2024. USD million.

https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2025/m08/cisco-reports-fourth-quarter-earnings.html
Publication: 2025-08-13. Issuer earnings-release publication. Retrieved 2026-10-09T10:53:27.276327+00:00.

https://www.cisco.com/c/dam/en_us/about/annual-report/2025-cisco-full-annual-report.pdf
Publication: None. Annual report signature/auditor date is 2025-09-03, publication date not independently established. Retrieved 2026-10-09T10:53:27.801122+00:00.

c07:s01 - Release consolidated income and cash-flow statements, annual columns
The August 13 release states annual GAAP income and cash flow before the supplier settlement. Source versions have the same fiscal-year endpoints and revenue scope. Non-GAAP figures are as initially released, with no subsequent non-GAAP recast supplied.

c07:s02 - Annual report pages 36, 57, 59 and 101, statements and Note 21
The annual report expressly supersedes the earnings release. The August 26 supplier settlement led to a Q4FY2025 USD 355 million product cost charge and USD 82 million tax benefit. No incremental cash consideration is paid. Supplier prepayments and escrow are stocks, not the expense or an additional cash outflow.

c07:s03 - Annual report pages 31 and 59, acquisition scope and operating cash
FY2025 includes a full year of Splunk versus roughly four months in FY2024, preventing an exact organic revenue-growth estimate from these totals alone. Changed net income, deferred taxes, inventory and other assets offset in operating cash. Both annual source versions report USD 14,193 million operating cash.

Source-derived observations

{
  "income_versions": [
    {
      "version": "release",
      "year": 2025,
      "product_revenue_usd_million": 41608,
      "service_revenue_usd_million": 15046,
      "product_cost_usd_million": 14766,
      "service_cost_usd_million": 4743,
      "operating_expense_usd_million": 25030,
      "other_income_usd_million": -660,
      "tax_usd_million": 1002,
      "net_income_usd_million": 10453
    },
    {
      "version": "annual",
      "year": 2025,
      "product_revenue_usd_million": 41608,
      "service_revenue_usd_million": 15046,
      "product_cost_usd_million": 15121,
      "service_cost_usd_million": 4743,
      "operating_expense_usd_million": 25030,
      "other_income_usd_million": -660,
      "tax_usd_million": 920,
      "net_income_usd_million": 10180
    },
    {
      "version": "release",
      "year": 2024,
      "product_revenue_usd_million": 39253,
      "service_revenue_usd_million": 14550,
      "product_cost_usd_million": 14339,
      "service_cost_usd_million": 4636,
      "operating_expense_usd_million": 22647,
      "other_income_usd_million": 53,
      "tax_usd_million": 1914,
      "net_income_usd_million": 10320
    },
    {
      "version": "annual",
      "year": 2024,
      "product_revenue_usd_million": 39253,
      "service_revenue_usd_million": 14550,
      "product_cost_usd_million": 14339,
      "service_cost_usd_million": 4636,
      "operating_expense_usd_million": 22647,
      "other_income_usd_million": 53,
      "tax_usd_million": 1914,
      "net_income_usd_million": 10320
    }
  ],
  "cash_versions": [
    {
      "version": "release",
      "year": 2025,
      "measure": "net_income",
      "amount_usd_million": 10453
    },
    {
      "version": "release",
      "year": 2025,
      "measure": "deferred_tax",
      "amount_usd_million": -1051
    },
    {
      "version": "release",
      "year": 2025,
      "measure": "inventory_change",
      "amount_usd_million": 278
    },
    {
      "version": "release",
      "year": 2025,
      "measure": "other_asset_change",
      "amount_usd_million": -923
    },
    {
      "version": "release",
      "year": 2025,
      "measure": "operating_cash",
      "amount_usd_million": 14193
    },
    {
      "version": "annual",
      "year": 2025,
      "measure": "net_income",
      "amount_usd_million": 10180
    },
    {
      "version": "annual",
      "year": 2025,
      "measure": "deferred_tax",
      "amount_usd_million": -1133
    },
    {
      "version": "annual",
      "year": 2025,
      "measure": "inventory_change",
      "amount_usd_million": 209
    },
    {
      "version": "annual",
      "year": 2025,
      "measure": "other_asset_change",
      "amount_usd_million": -499
    },
    {
      "version": "annual",
      "year": 2025,
      "measure": "operating_cash",
      "amount_usd_million": 14193
    }
  ],
  "settlement": [
    {
      "economic_date": "2025-08-26",
      "fiscal_year_charged": 2025,
      "product_cost_charge_usd_million": 355,
      "tax_benefit_usd_million": 82,
      "incremental_cash_consideration_usd_million": 0
    }
  ]
}
