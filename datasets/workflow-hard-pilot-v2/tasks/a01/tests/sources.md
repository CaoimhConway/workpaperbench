# Source dossier

Annual Report & Accounts 2025

https://ir.sunbeltrentals.com/_assets/_aea60f2cfa9dfbc336809022ddff8808/sunbeltrentals/db/3746/34974/annual_report/Ashtead_Annual_Report_2025_.pdf

Source date 2025-07-24. Issuer posting announcement dated July 24, 2025 confirms the report had been issued. Exact initial online publication time is unknown. Facility disclosures are whole USD million, with the commitment stated as USD 4.75 billion and normalized to million. Planning inputs are authored point values. The source reports covenant availability separately from unused commitment. The scenario does not infer a missing reconciliation.

## a01:s01

Note 18 Borrowings, printed p.149, PDF p.151, First priority senior secured credit facility, first paragraph

authentic_source_facts

https://ir.sunbeltrentals.com/_assets/_aea60f2cfa9dfbc336809022ddff8808/sunbeltrentals/db/3746/34974/annual_report/Ashtead_Annual_Report_2025_.pdf

At April 30, 2025 the ABL commitment was USD 4.75 billion through November 2029. Utilisation of USD 1,351 million includes USD 5 million of letters of credit. The facility has first-priority security over substantially all group assets. Pricing uses average availability and a base rate plus 125 to 137.5 basis points. The reported weighted borrowing rate was 5.242 percent.

## a01:s02

Note 18 Borrowings, printed p.149, PDF p.151, second and third paragraphs

authentic_source_facts

https://ir.sunbeltrentals.com/_assets/_aea60f2cfa9dfbc336809022ddff8808/sunbeltrentals/db/3746/34974/annual_report/Ashtead_Annual_Report_2025_.pdf

The sole financial-performance covenant is a ratio of at least 1.0. Its numerator is last-twelve-month EBITDA before exceptional items less net capital expenditure paid in cash. Its denominator sums scheduled debt repayment, cash interest, cash tax and paid dividends over that period. The test is inapplicable when availability exceeds USD 475 million. Availability means borrowing base less facility utilisation. Reported covenant-purpose availability was USD 3,616 million, with a further USD 6,194 million described as suppressed availability. The covenant was not measured at that date. The extract does not explain why covenant-purpose availability differs from commitment less utilisation.

## a01:s03

Financial review, Debt facilities, printed p.48, PDF p.50

authentic_source_facts

https://ir.sunbeltrentals.com/_assets/_aea60f2cfa9dfbc336809022ddff8808/sunbeltrentals/db/3746/34974/annual_report/Ashtead_Annual_Report_2025_.pdf

This section independently repeats the commitment of USD 4.75 billion, utilisation of USD 1,351 million including USD 5 million letters of credit, the 1.0 fixed-charge requirement, the same numerator and denominator definitions as Note 18, the exemption when availability exceeds USD 475 million, USD 3,616 million availability and USD 6,194 million suppressed availability. It also reports that the ratio exceeded the requirement at April 30, 2025.

## a01:s04

Authored twelve-month funding scenarios and analysis scope

authored_assumption

All amounts in facility, planning_cases, proposals and equity_targets are USD million, except new_debt_cash_rate, an annual decimal rate. facility contains source observations. The other tables are authored planning assumptions, not issuer forecasts. Use the disclosed covenant summary as the complete financial-performance test for this exercise. All other draw conditions are satisfied. No commitment increase, accordion, refinancing or alternative debt is available. Keep the separately reported covenant availability independent of unused commitment. Its difference from commitment less utilisation is not explained by the supplied extract. Additional cash borrowing increases utilisation and reduces covenant availability dollar for dollar. Letters of credit and the borrowing base otherwise remain unchanged. The supplied new_debt_cash_rate is the full cash cost of additional borrowing for the whole planning period. It replaces the disclosed rate grid only for these scenarios. Existing cash interest is already included in planning_cases. Scheduled principal repays debt outside this ABL and does not restore ABL drawing capacity. Each planning case covers one simultaneous pro forma twelve-month test period. Use its EBITDA before exceptional items, net capital expenditure paid in cash, scheduled principal, existing cash interest, cash tax and ordinary dividends on the disclosed covenant basis. No IFRS-to-covenant adjustment is required. Working-capital outflow is an additional cash use outside those amounts. Opening usable cash above the required operating cash floor is zero. EBITDA is cash generated before the listed cash uses and working-capital outflow. There are no other cash flows. Ending cash must remain at or above that floor. A special dividend is paid in cash in the same test period and is a dividend for covenant purposes. Borrowing and cash equity are nonnegative continuous amounts. Cash equity has no fees, interest or effect on EBITDA, fixed charges or the borrowing base. It is available solely in equity_support. No intra-period liquidity path or covenant cure by increasing EBITDA is modeled. An upper or lower limit is the sharp supremum or infimum over the allowed funding choices. attainable is 1 only if a feasible choice reaches the exact limit and 0 otherwise. Do not round a strict covenant trigger into an inclusive exemption.

## Normalized input tables

Table origins distinguish source facts from authored scenarios. Full source documents are not redistributed.

### facility

authentic_source_facts

```json
[
  {
    "commitment": 4750,
    "utilised_including_lc": 1351,
    "letters_of_credit": 5,
    "covenant_availability": 3616,
    "test_threshold": 475,
    "suppressed_availability": 6194
  }
]
```

### planning_cases

authored_assumption

```json
[
  {
    "scenario": "case_a",
    "ebitda": 4900,
    "net_cash_capex": 2200,
    "scheduled_principal": 500,
    "existing_cash_interest": 500,
    "cash_tax": 300,
    "ordinary_dividend": 400,
    "working_capital_outflow": 3000,
    "new_debt_cash_rate": 0.08
  },
  {
    "scenario": "case_b",
    "ebitda": 5200,
    "net_cash_capex": 2200,
    "scheduled_principal": 500,
    "existing_cash_interest": 500,
    "cash_tax": 300,
    "ordinary_dividend": 400,
    "working_capital_outflow": 3300,
    "new_debt_cash_rate": 0.08
  },
  {
    "scenario": "case_c",
    "ebitda": 5900,
    "net_cash_capex": 2200,
    "scheduled_principal": 500,
    "existing_cash_interest": 500,
    "cash_tax": 300,
    "ordinary_dividend": 400,
    "working_capital_outflow": 4000,
    "new_debt_cash_rate": 0.08
  }
]
```

### proposals

authored_assumption

```json
[
  {
    "proposal": "p800",
    "special_dividend": 800
  },
  {
    "proposal": "p1000",
    "special_dividend": 1000
  },
  {
    "proposal": "p1100",
    "special_dividend": 1100
  }
]
```

### equity_targets

authored_assumption

```json
[
  {
    "target": "t1000",
    "special_dividend": 1000
  },
  {
    "target": "t1400",
    "special_dividend": 1400
  }
]
```

Attributed factual observations and concise definitions only. Issuer material is excluded from the project MIT license. Full source documents are not redistributed.
