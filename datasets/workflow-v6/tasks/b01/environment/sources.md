# Brale SBC reserve report dictionary

## Measurement scope
The table contains two Brale SBC reserve report snapshots. SBC issued is the report's total SBC supply across its supported blockchains at that report date. The May and June reports list the same 13 chains: Arbitrum, Avalanche, Base, Canton, Celo, Coreum, Ethereum, Ethereum Classic, Hedera, Optimism, Polygon, Solana and Stellar. Values are whole USD and SBC units.

## Reserve assets
The reports define fair value of reserve assets as the total balance of U.S.-denominated assets held by Brale in unencumbered accounts segregated from its other accounts. Each report lists cash and cash equivalents, U.S. government backed debt, and fair value of reserve assets. The documents do not describe a separate valuation method for each component. Their opinions compare reserve asset value with SBC in circulation.

## Observation and report dates
The economic observation dates are May 31 and June 30, 2025, each at 11:50 p.m. Eastern Time. The reports are dated June 12 and July 16, respectively. These are report dates, not evidence of historical first-publication timestamps. Both observations are month-end stocks.

## Examiner scope
The May document is an Abdo independent accountant report that describes examination under AICPA attestation standards. The June document is a Michael Coglianese, CPA, P.C. performance attestation. It states that the examiner relied on records supplied by Brale and was not retained to independently confirm their authenticity and accuracy. The examiner identity and described scope differ between the reports.

## Interpretation boundary
Neither report gives a secondary-market quote, a realized redemption result, a liquidation estimate, or instrument-level reserve holdings. The published asset categories are aggregates and do not independently establish each underlying record's authenticity or current marketability.

## Source locators
May report: https://brale.xyz/assets/reports/SBC-Stable-Coin-Reserve-Attestation-Report-05-2025.pdf
June report: https://brale.xyz/assets/reports/SBC-Stable-Coin-Reserve-Attestation-Report-06-2025.pdf
The table values and criteria are on page 2. The as-of date and examiner statements are on page 1.

## Source-derived observation tables

These are faithful normalized source observations, not target calculations.

reserve_reports
[
  {
    "report_date": "2025-05-31",
    "as_of_et": "2025-05-31 23:50 ET",
    "report_signed_date": "2025-06-12",
    "examiner": "Abdo independent accountant report",
    "issued_sbc": 7093795,
    "cash_equivalents_usd": 2210784,
    "us_government_debt_usd": 4883011,
    "reported_reserve_fv_usd": 7093795
  },
  {
    "report_date": "2025-06-30",
    "as_of_et": "2025-06-30 23:50 ET",
    "report_signed_date": "2025-07-16",
    "examiner": "Michael Coglianese CPA PC performance attestation",
    "issued_sbc": 9356516,
    "cash_equivalents_usd": 3475633,
    "us_government_debt_usd": 5880883,
    "reported_reserve_fv_usd": 9356516
  }
]
