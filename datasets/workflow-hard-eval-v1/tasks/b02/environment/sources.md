# Source dossier

Reddit December 2023 issued capital and pre-IPO liquidation rights

https://www.sec.gov/Archives/edgar/data/1713445/000162828024012380/reddit-final424b4.htm

Source date 2024-03-21.  Exact issued share counts and the four-decimal charter issue prices are retained. Scenario arithmetic treats their displayed precision as fixed. The prospectus aggregate preferences and carrying amounts are in USD thousands, normalized to millions. Do not force computed contractual preferences to the rounded aggregate observations. Publication dates are SEC filing dates. The prospectus itself is dated March 20, 2024.

## b02:s01

Consolidated Balance Sheets, F-3, December 31, 2023 actual column. Note 12, F-23 to F-25, preferred-capital table, Dividends and Conversion. Note 13, F-25, common stock rights.

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1713445/000162828024012380/reddit-final424b4.htm

Issued and outstanding common stock is 7,099,700 Class A and 53,904,204 Class B shares. The preferred table records 73,021,449 shares in nine series, with the per-series counts, aggregate liquidation preferences and net carrying amounts retained in preferred. These are actual balances, not IPO pro forma shares or authorized shares. Each preferred series has a 1:1 common-stock conversion ratio. Series F-1 converts to Class A and the others to Class B. No dividends were declared or paid through December 31, 2023. Common A and B economic rights are identical, while votes per share differ.

## b02:s02

Pre-IPO certificate of incorporation, section IV.E.1(d), printed p. 8, and IV.E.3(a)-(b), pp. 15-16.

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1713445/000162828024006294/exhibit31-sx1.htm

Original issue prices by series are A 2.6667, A-1 5.9259, B 6.2631, C 15.7739, D and D-1 21.6863, E 42.4742, F and F-1 61.7944 USD. Series A has a 1.75-times liquidation preference. Every other series has a 1-times preference. Declared unpaid dividends are additional. Unconverted A-1 is junior to all other preferred series. Within a priority rank, insufficient proceeds are allocated in proportion to full preferential entitlements.

## b02:s03

Pre-IPO certificate, sections IV.E.3(a), IV.E.3(c)-(d), pp. 15-16, and IV.E.5(p)(i), p. 26.

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1713445/000162828024006294/exhibit31-sx1.htm

A Liquidation Event valuing the company at more than USD 240,000,000 automatically converts Series A and A-1 into Class B common stock. Residual proceeds go to common holders in proportion to shares. Preferred holders are deemed converted when conversion would deliver a greater aggregate distribution. A converted holder no longer receives a preferred distribution. Other conversion triggers include a qualified public offering and specified shareholder elections.

## b02:s04

Note 12, Convertible Preferred Stock, F-23 to F-25, Liquidation Preference and Conversion. Note 13, F-25.

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1713445/000162828024012380/reddit-final424b4.htm

Unconverted A-1 ranks after the other preferred series and before common. Senior shortfalls are allocated by full preference. Holders may convert 1:1 instead. A and A-1 automatically convert in a liquidation valuing Reddit above USD 240 million. Common classes have equal economic rights.

## b02:s05

Authored liquidation offers, owner cash targets and interpretation of the contractual valuation trigger.

authored_assumption

authored:workflow-hard-eval-v1/b02

sale_cases and owner_targets are authored sensitivities, not observed transactions or issuer forecasts. For these hypothetical cash liquidations, trigger valuation equals the proceeds distributable to the listed issued stock. Issued capital and displayed charter terms remain frozen. All necessary approvals are assumed, with no waiver, new dividends or other conversion event. Unissued awards and all other claims are settled outside this pool without new shares. No amount for those excluded settlements is supplied or inferred.

## b02:s06

Note 13, F-25, Common Stock Reserved for Issuance. Note 14, F-29, stock-option activity table and following paragraph.

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1713445/000162828024012380/reddit-final424b4.htm

Outstanding options cover 29,795,909 common shares with weighted-average exercise price USD 17.83. Outstanding RSUs cover 27,627,171 shares. These are potentially issuable rather than issued shares. The retained excerpts omit some award-specific vesting, exercise and change-of-control settlement terms.

## Normalized input tables

Table origins distinguish source facts from authored scenarios. Full source documents are not redistributed.

### preferred

authentic_source_facts

```json
[
  {
    "series": "A",
    "shares": 7500000,
    "reported_preference": 35,
    "carrying": 21.67
  },
  {
    "series": "A-1",
    "shares": 114746,
    "reported_preference": 0.68,
    "carrying": 0.68
  },
  {
    "series": "B",
    "shares": 17564937,
    "reported_preference": 110.011,
    "carrying": 130.567
  },
  {
    "series": "C",
    "shares": 10073589,
    "reported_preference": 158.9,
    "carrying": 158.048
  },
  {
    "series": "D",
    "shares": 10290493,
    "reported_preference": 223.163,
    "carrying": 223.092
  },
  {
    "series": "D-1",
    "shares": 3543124,
    "reported_preference": 76.837,
    "carrying": 76.687
  },
  {
    "series": "E",
    "shares": 12195638,
    "reported_preference": 518.002,
    "carrying": 517.577
  },
  {
    "series": "F",
    "shares": 6634905,
    "reported_preference": 410,
    "carrying": 409.862
  },
  {
    "series": "F-1",
    "shares": 5104017,
    "reported_preference": 315.4,
    "carrying": 315.309
  }
]
```

### common

authentic_source_facts

```json
[
  {
    "security": "common_A",
    "shares": 7099700
  },
  {
    "security": "common_B",
    "shares": 53904204
  }
]
```

### terms

authentic_source_facts

```json
[
  {
    "series": "A",
    "issue_price": 2.6667,
    "preference_multiple": 1.75,
    "conversion_ratio": 1,
    "rank": 1,
    "forced_eligible": 1
  },
  {
    "series": "A-1",
    "issue_price": 5.9259,
    "preference_multiple": 1,
    "conversion_ratio": 1,
    "rank": 2,
    "forced_eligible": 1
  },
  {
    "series": "B",
    "issue_price": 6.2631,
    "preference_multiple": 1,
    "conversion_ratio": 1,
    "rank": 1,
    "forced_eligible": 0
  },
  {
    "series": "C",
    "issue_price": 15.7739,
    "preference_multiple": 1,
    "conversion_ratio": 1,
    "rank": 1,
    "forced_eligible": 0
  },
  {
    "series": "D",
    "issue_price": 21.6863,
    "preference_multiple": 1,
    "conversion_ratio": 1,
    "rank": 1,
    "forced_eligible": 0
  },
  {
    "series": "D-1",
    "issue_price": 21.6863,
    "preference_multiple": 1,
    "conversion_ratio": 1,
    "rank": 1,
    "forced_eligible": 0
  },
  {
    "series": "E",
    "issue_price": 42.4742,
    "preference_multiple": 1,
    "conversion_ratio": 1,
    "rank": 1,
    "forced_eligible": 0
  },
  {
    "series": "F",
    "issue_price": 61.7944,
    "preference_multiple": 1,
    "conversion_ratio": 1,
    "rank": 1,
    "forced_eligible": 0
  },
  {
    "series": "F-1",
    "issue_price": 61.7944,
    "preference_multiple": 1,
    "conversion_ratio": 1,
    "rank": 1,
    "forced_eligible": 0
  }
]
```

### trigger

authentic_source_facts

```json
[
  {
    "valuation": 240.0
  }
]
```

### sale_cases

authored_assumption

```json
[
  {
    "sale_case": "v200",
    "proceeds": 200
  },
  {
    "sale_case": "v240",
    "proceeds": 240
  },
  {
    "sale_case": "v241",
    "proceeds": 241
  },
  {
    "sale_case": "v1850",
    "proceeds": 1850
  },
  {
    "sale_case": "v2500",
    "proceeds": 2500
  },
  {
    "sale_case": "v4000",
    "proceeds": 4000
  },
  {
    "sale_case": "v6000",
    "proceeds": 6000
  },
  {
    "sale_case": "v9000",
    "proceeds": 9000
  }
]
```

### owner_targets

authored_assumption

```json
[
  {
    "target_case": "A_4",
    "security": "A",
    "cash_target": 4
  },
  {
    "target_case": "A_10",
    "security": "A",
    "cash_target": 10
  },
  {
    "target_case": "F_54",
    "security": "F",
    "cash_target": 54
  },
  {
    "target_case": "common_A_50",
    "security": "common_A",
    "cash_target": 50
  },
  {
    "target_case": "common_B_2000",
    "security": "common_B",
    "cash_target": 2000
  }
]
```

Attributed financial facts and concise contract definitions only. Issuer material is excluded from the project MIT license. Full source documents are not redistributed.
