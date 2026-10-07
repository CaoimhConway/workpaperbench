# Ripple RLUSD reserve report dictionary

The May report observations are May 22 and May 30, 2025 at 5:00 p.m. Eastern Time. The June report observations are June 9 and June 30, 2025 at 5:00 p.m. Eastern Time. The May report was signed June 23, 2025, and the June report was signed July 24, 2025. These are report/signature dates, not observation dates or known historical publication timestamps.

RLUSD outstanding means issued, outstanding, redeemable tokens currently present on XRPL and Ethereum at each report date. Reserve assets are USD-denominated accounts established for holders and segregated from proprietary company assets. Market value is determined as of trade date and fair value as of each report date. Asset classes include bank deposits, government money-market funds, and U.S. Treasury bills with maturities of three months or less.

`reserve_components` contains USD asset-class amounts for all four report observations. The June 30 Treasury-bill dash is represented as zero. `reported_balances` contains the reported circulating amount and reserve value for each observation. The May 30 and June 30 observations are month-end comparisons at the same stated time of day. The reports also include observations for May 22 and June 9 at the same stated time of day.

## Source sections

b04:s01 - May report, PDF page 3, printed page 2. May 22 and May 30, 2025 observations at 5:00 p.m. Eastern Time.
- May 22: circulating RLUSD 310,543,072, reported reserve USD 323,349,533.
- May 30: circulating RLUSD 309,043,794, reported reserve USD 322,099,766.

b04:s02 - May report reserve components, PDF page 3, printed page 2. USD asset-class amounts by date:
- 2025-05-22: U.S. Treasury bills 181,273,927, government money-market funds 97,445,721, cash deposits 44,629,885.
- 2025-05-30: U.S. Treasury bills 181,364,719, government money-market funds 97,606,162, cash deposits 43,128,885.

b04:s03 - June report, PDF page 3, printed page 2. June 9 and June 30, 2025 observations at 5:00 p.m. Eastern Time.
- June 9: circulating RLUSD 388,743,694, reported reserve USD 402,390,351.
- June 30: circulating RLUSD 455,243,694, reported reserve USD 471,227,699.

b04:s04 - June report reserve components, PDF page 3, printed page 2. USD asset-class amounts by date:
- 2025-06-09: U.S. Treasury bills 211,474,620, government money-market funds 113,698,252, cash deposits 77,217,479.
- 2025-06-30: U.S. Treasury bills 0, government money-market funds 400,580,147, cash deposits 70,647,552.

b04:s05 - Both reports define outstanding RLUSD as issued, outstanding, redeemable tokens present on XRPL and Ethereum.

b04:s06 - Reserves are USD-denominated, held for holders and segregated from company proprietary assets. Market value is determined at trade date and fair value at report date. The reports were signed June 23 and July 24, 2025. Historical publication times are unknown.
