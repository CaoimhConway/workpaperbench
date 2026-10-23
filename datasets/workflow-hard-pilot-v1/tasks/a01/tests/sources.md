# Source dossier

Fourth quarter and Full year 2016 summary report

https://www.sec.gov/Archives/edgar/data/869425/000119312517066172/d352780dex1.htm

Published 2017-03-01. Amounts published in whole EUR million. Compute from displayed amounts without reverse-engineering rounded percentage growth. Selected columns retain necessary facts without the redundant derived pro forma Q4 segment totals or adjusted full-year 2015 targets.

## a01:s01

pp. 2-3, Basis of preparation and calendar footnotes

IFRS consolidates former Delhaize from July 24, 2016. Pro forma treats the merger as occurring at the start of the 2015 financial year and includes remedy-store and other divestment adjustments. It is hypothetical comparative information, not actual historical combined results. Former Ahold FY/Q4: 2016 52/12 weeks, 2015 53/13. Former Delhaize FY/Q4: 52/13 in both years. The pro forma calendars remain different across the former groups. The 2016 Q4 calendar adjustment reinstates October 1-9 for European Delhaize and the corresponding October 2-9 U.S. period excluded from the IFRS presentation. CSE includes former Ahold Czech operations and former Delhaize Greece, Romania and Serbia.

## a01:s02

p. 34, Pro forma net sales by segment Q4 2016, IFRS and adjustment columns

Selected factual table columns are normalized below.

## a01:s03

pp. 4-7, segment pro forma net sales, FY 2016, FY 2015 and Q4 2015 EUR columns

Selected factual table columns are normalized below.

## a01:s04

p. 2, Pro forma net sales after adjustment for week 53, adjusted Q4 2015 column

Selected factual table columns are normalized below.

## a01:s05

p. 2, Group performance IFRS and pro forma net sales, FY columns

Selected factual table columns are normalized below.

## Normalized input tables

These retain source observations. stress_rates, where present, contains authored scenario assumptions. Full source documents are not redistributed.

### quarter_current

```json
[
  {
    "segment": "ahold_usa",
    "ifrs": 5690,
    "divestments": -100,
    "calendar": 0
  },
  {
    "segment": "delhaize_america",
    "ifrs": 3675,
    "divestments": -9,
    "calendar": 303
  },
  {
    "segment": "netherlands",
    "ifrs": 3226,
    "divestments": -18,
    "calendar": 0
  },
  {
    "segment": "belgium",
    "ifrs": 1164,
    "divestments": -5,
    "calendar": 121
  },
  {
    "segment": "cse",
    "ifrs": 1364,
    "divestments": 0,
    "calendar": 94
  }
]
```

### period_sales

```json
[
  {
    "segment": "ahold_usa",
    "fy2016": 23316,
    "fy2015": 23106,
    "q42015": 5903
  },
  {
    "segment": "delhaize_america",
    "fy2016": 15501,
    "fy2015": 15146,
    "q42015": 3822
  },
  {
    "segment": "netherlands",
    "fy2016": 13015,
    "fy2015": 12624,
    "q42015": 3245
  },
  {
    "segment": "belgium",
    "fy2016": 4942,
    "fy2015": 4859,
    "q42015": 1293
  },
  {
    "segment": "cse",
    "fy2016": 5557,
    "fy2015": 5146,
    "q42015": 1404
  }
]
```

### matched_quarter

```json
[
  {
    "segment": "ahold_usa",
    "q42015_matched": 5451
  },
  {
    "segment": "delhaize_america",
    "q42015_matched": 3822
  },
  {
    "segment": "netherlands",
    "q42015_matched": 2983
  },
  {
    "segment": "belgium",
    "q42015_matched": 1293
  },
  {
    "segment": "cse",
    "q42015_matched": 1373
  }
]
```

### group_annual

```json
[
  {
    "year": 2015,
    "ifrs": 38203,
    "proforma": 60881
  },
  {
    "year": 2016,
    "ifrs": 49695,
    "proforma": 62331
  }
]
```

Attributed factual observations and concise definitions only. Issuer material is excluded from the project MIT license. Full source documents are not redistributed.
