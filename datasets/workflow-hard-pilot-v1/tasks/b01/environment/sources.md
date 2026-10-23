# Source dossier

2025 annual report

https://www.microsoft.com/investor/reports/ar25/index.html

Published 2025-07-30. Balance-sheet and lease amounts are whole USD million. PPE depreciation and capital payables are one-decimal USD billion, retained in those input units. Outputs use displayed-value arithmetic and cannot imply more precise underlying observations. cash_ppe is the positive magnitude of the investing cash outflow, accumulated depreciation is positive contra-asset magnitude. Financing lease cash is principal and finance-lease cash classified in operating activities is interest.

## b01:s01

Consolidated cash flows, year ended June 30, 2025

Selected factual table columns are normalized below.

## b01:s02

Note 6, Property and Equipment, June 30, 2025 and 2024 and following paragraphs

Depreciation expense for FY2025 is USD 22.0 billion. Purchases of PPE remaining in accounts payable at June 30, 2025 and 2024 are USD 6.9 billion and USD 4.3 billion. These three observations are rounded to one decimal billion.

## b01:s03

Note 13, Leases, lease cost and supplemental cash flow tables FY2025 and finance-lease balance sheet table June 30, 2025 and 2024

Selected factual table columns are normalized below.

## b01:s04

Note 1, Accounting Policies, Property and Equipment and Leases

PPE is stated at cost less accumulated depreciation. Finance leases are included in PPE. Operating lease right-of-use assets are presented separately.

## Normalized input tables

These retain source observations. stress_rates, where present, contains authored scenario assumptions. Full source documents are not redistributed.

### cash_flows

```json
[
  {
    "year": 2025,
    "cash_ppe": 64551,
    "cfo": 136162,
    "depreciation_amortization_other": 34153
  }
]
```

### ppe

```json
[
  {
    "year": 2024,
    "gross": 212012,
    "accumulated": 76421,
    "net": 135591,
    "capital_payables_billion": 4.3
  },
  {
    "year": 2025,
    "gross": 298619,
    "accumulated": 93653,
    "net": 204966,
    "capital_payables_billion": 6.9
  }
]
```

### finance_leases

```json
[
  {
    "year": 2024,
    "gross": 32248,
    "accumulated": 6386,
    "net": 25862
  },
  {
    "year": 2025,
    "gross": 53876,
    "accumulated": 9861,
    "net": 44015
  }
]
```

### annual_expenses

```json
[
  {
    "year": 2025,
    "ppe_depreciation_billion": 22.0,
    "finance_amortization": 3408,
    "finance_rou_additions": 20511,
    "finance_principal_cash": 2283,
    "finance_interest_cash": 1372
  }
]
```

Attributed factual observations and concise definitions only. Issuer material is excluded from the project MIT license. Full source documents are not redistributed.
