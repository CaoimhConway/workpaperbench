# Source dossier

Veeco year-end 2024 convertible notes, indentures and EPS accounting definitions

https://www.sec.gov/Archives/edgar/data/103145/000155837025001001/veco-20241231x10k.htm

Source date 2025-02-14.  The annual report monetary and share tables are in thousands, normalized to millions without increasing observation precision. Contract rates retain their displayed digits. The reported 2029 rate of 34.21852 is preserved separately and the explicit scenario uses contractual 34.2185. The expense observations are actual FY2024 expenses, not annualized maturities or new coupon forecasts. Dates on contract evidence are executed-document dates. Synthetic controls are separately identified and do not revise historical observations.

## b01:s01

Note 11, Convertible Senior Notes, F-27 to F-28, December 31, 2024 carrying-value table and conversion paragraph

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/103145/000155837025001001/veco-20241231x10k.htm

Outstanding face principal is 26.500, 25.000 and 230.000 million for the 2025, 2027 and 2029 notes. The corresponding net carrying amounts are 26.496, 24.777 and 224.925 million. Maturities are January 15, 2025, June 1, 2027 and June 1, 2029. The 10-K reports conversion rates 41.6667, 71.5372 and 34.21852 and approximate conversion prices 24.00, 13.98 and 29.22. The contractual rate for 2029 differs in the last displayed digits.

## b01:s02

Note 11, F-29, total interest expense table, FY2024 columns

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/103145/000155837025001001/veco-20241231x10k.htm

FY2024 coupon interest is 0.928, 0.938 and 6.613 million for the 2025, 2027 and 2029 notes. Debt discount and transaction-cost amortization is 0.098, 0.090 and 1.069 million, respectively.

## b01:s03

Executed indenture, section 14.01(a), p. 40, and section 14.02(a)(iv)(A)

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/103145/000110465920126397/tm2036203d1_ex4-1.htm

The initial rate is 41.6667 common shares for each USD 1,000 principal. Physical settlement delivers the conversion-rate quantity of shares for each USD 1,000 converted. The issuer can elect physical, cash or combination settlement.

## b01:s04

Executed indenture, section 14.01(a), p. 54, and section 14.02(a)(iv)(A)

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/103145/000110465920063205/tm2020001d1_ex4-1.htm

The initial rate is 71.5372 common shares for each USD 1,000 principal. Physical settlement delivers the conversion-rate quantity of shares for each USD 1,000 converted. The issuer can elect physical, cash or combination settlement.

## b01:s05

Executed indenture, section 14.01(a), p. 54, section 14.02(a), p. 57, and Daily Conversion Value, Daily Measurement Value, Daily Settlement Amount definitions, pp. 3-4

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/103145/000110465923063141/tm2316279d1_ex4-1.htm

The initial rate is 34.2185 shares for each USD 1,000 principal. Conversion settlement aggregates 60 observation days. Daily conversion value is one sixtieth of the conversion rate times daily VWAP. Daily measurement value is USD 1,000 divided by 60. Daily cash is the lower of these two values. Above that measurement value, an elected zero cash percentage delivers the excess value in shares at daily VWAP.

## b01:s06

Note 2, Income (Loss) Per Share, F-16, introductory accounting paragraph and FY2024 table. Note 11, F-29, Capped Call Transactions

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/103145/000155837025001001/veco-20241231x10k.htm

For diluted EPS, the 2025 and 2027 notes use the maximum shares issuable when dilutive because the issuer may settle in cash or shares. For 2029, mandatory cash principal means only shares for excess conversion value enter when dilutive. FY2024 basic weighted shares are 56.426 million and incremental awards are 1.010 million. Net income is 73.714 million, convertible-note interest added back is 2.054 million and the adjusted numerator is 75.768 million. Reported note dilution is 4.160 million and total diluted weighted shares are 61.596 million. Capped calls are separate transactions and do not change noteholders' rights.

## b01:s07

ASU 2015-01, printed p. 19 (PDF page 25), amended ASC 260-10-45-18

authentic_source_facts

https://storage.fasb.org/ASU%202015-01.pdf

Potential common share issues are considered individually in order from the lowest to highest earnings per incremental share to obtain maximum dilution. An issue dilutive by itself can be antidilutive when considered with other issues. Options and warrants normally come first because they do not adjust the numerator. The controlling earnings measure is income from continuing operations available to common shareholders.

## b01:s08

Authored maturity, full-period earnings and reverse-threshold scenarios

authored_assumption

authored:workflow-hard-pilot-v2/b01

The tables price_cases, income_cases and threshold_case contain authored scenarios, not issuer forecasts. Contractual balances, rates, EPS basis and reported expenses retain the dates and scope above. The output contract specifies the settlement elections, frozen full-period EPS scope, no additional tax adjustment and excluded separate hedges.

## Normalized input tables

Table origins distinguish source facts from authored scenarios. Full source documents are not redistributed.

### notes

authentic_source_facts

```json
[
  {
    "note": "2025",
    "maturity": "2025-01-15",
    "principal": 26.5,
    "carrying": 26.496,
    "coupon": 0.928,
    "amortization": 0.098
  },
  {
    "note": "2027",
    "maturity": "2027-06-01",
    "principal": 25,
    "carrying": 24.777,
    "coupon": 0.938,
    "amortization": 0.09
  },
  {
    "note": "2029",
    "maturity": "2029-06-01",
    "principal": 230,
    "carrying": 224.925,
    "coupon": 6.613,
    "amortization": 1.069
  }
]
```

### contract_terms

authentic_source_facts

```json
[
  {
    "note": "2025",
    "conversion_rate": 41.6667,
    "principal_settlement": "choice"
  },
  {
    "note": "2027",
    "conversion_rate": 71.5372,
    "principal_settlement": "choice"
  },
  {
    "note": "2029",
    "conversion_rate": 34.2185,
    "principal_settlement": "cash"
  }
]
```

### reported_rates

authentic_source_facts

```json
[
  {
    "note": "2025",
    "conversion_rate": 41.6667
  },
  {
    "note": "2027",
    "conversion_rate": 71.5372
  },
  {
    "note": "2029",
    "conversion_rate": 34.21852
  }
]
```

### eps_basis

authentic_source_facts

```json
[
  {
    "basic_shares": 56.426,
    "award_shares": 1.01,
    "reported_income": 73.714,
    "reported_note_addback": 2.054
  }
]
```

### price_cases

authored_assumption

```json
[
  {
    "price_case": "p12",
    "price": 12
  },
  {
    "price_case": "p18",
    "price": 18
  },
  {
    "price_case": "p25",
    "price": 25
  },
  {
    "price_case": "p40",
    "price": 40
  }
]
```

### income_cases

authored_assumption

```json
[
  {
    "income_case": "low",
    "income": 10
  },
  {
    "income_case": "middle",
    "income": 40
  },
  {
    "income_case": "near_boundary",
    "income": 55
  },
  {
    "income_case": "high",
    "income": 60
  },
  {
    "income_case": "reported",
    "income": 73.714
  }
]
```

### threshold_case

authored_assumption

```json
[
  {
    "price": 40,
    "target_shares": 5
  }
]
```

Attributed financial facts and concise accounting and contract definitions only. Issuer and FASB material is excluded from the project MIT license. Full source documents are not redistributed.
