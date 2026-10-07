# Circle USDC reserve report dictionary

The source report's observation cutoffs are March 19 and March 31, 2025 at 11:59 p.m. UTC. Each observation is a point-in-time balance. The printed report date is April 30, 2025. It is not a historical first-publication timestamp.

USDC circulation means total supply on approved chains less Tokens Allowed But Not Issued and Access Denied Tokens. The reserve fair-value definition covers USD-denominated assets in the Circle Reserve Fund and segregated accounts at regulated financial institutions for USDC holders. The reserve schedule includes component fair values and signed net timing adjustments. All reserve amounts are USD, and circulation amounts are USDC.

`reserve_components` contains source line items by observation date. CUSIP identifies a Treasury security. Negative values preserve the report's parenthetical timing adjustments. `reported_reserve_totals` contains the report's stated reserve total for reconciliation. `circulation_inputs` contains the source-defined supply categories. The report's circulation definition determines their relationship.

The two observations use the same stated definitions and UTC cutoff convention. The report's asset categories are aggregated reserve values. They do not provide instrument-level maturity, yield, liquidity, or independently observed redemption evidence.

## Source sections

b02:s02 - PDF page 3, 2025-03-19 reserve schedule. Treasury security fair values by CUSIP in USD: 912797KJ5 3,697,340,000, 912797MU8 1,178,373,594, 912797NT0 2,461,524,350, 912797MV6 797,482,547, 912797NY9 1,496,043,353, 912797NB9 414,075,741, 912797NZ6 1,244,690,340, 912797KS5 3,146,619,595, 912797PA9 1,569,885,088, 912797NC7 597,531,624, 912797PB7 962,266,781, 912797ND5 2,863,446,371, 912797PC5 1,790,887,406. Other listed components in USD: U.S. Treasury repurchase agreements 31,040,000,000, cash held in Circle Reserve Fund 1,000,774,222, cash due to/(owed by) Circle Reserve Fund due to timing and settlement differences, net -2,096,433,792, cash held at regulated financial institutions 7,067,110,474, cash due to/(owed by) Circle due to timing and settlement differences, net -84,025,566. Report-stated total reserve fair value is USD 59,147,592,128.

b02:s03 - PDF page 4, 2025-03-31 reserve schedule. Treasury security fair values by CUSIP in USD: 912797NT0 2,465,000,000, 912797MV6 1,423,464,525, 912797NY9 1,498,162,080, 912797NB9 1,063,968,331, 912797NZ6 1,096,587,717, 912797KS5 2,990,827,955, 912797PA9 1,521,318,728, 912797NC7 848,597,992, 912797PB7 134,455,689, 912797ND5 2,792,780,057, 912797PC5 1,793,382,181, 912797NE3 2,058,500,917, 912797PJ0 212,966,744, 912797PK7 2,930,554,574, 912797NN3 52,042,278, 912797NW3 1,979,957,220. Other listed components in USD: U.S. Treasury repurchase agreements 30,815,000,000, cash held in Circle Reserve Fund 1,004,149,953, cash due to/(owed by) Circle Reserve Fund due to timing and settlement differences, net -3,117,173,718, cash held at regulated financial institutions 6,592,595,197, cash due to/(owed by) Circle due to timing and settlement differences, net -116,431,379. Report-stated total reserve fair value is USD 60,040,707,040.

b02:s01 - PDF page 2, circulation and reserve criteria. Circulation is defined from total supply and the two stated excluded-token categories. Reserve fair value is the balance of USD-denominated assets held for holders in the Circle Reserve Fund and segregated financial-institution accounts.

b02:s04 - PDF page 2, March circulation table. Source inputs:
- 2025-03-19 supply categories in USDC: total supply 60,459,258,338, Tokens Allowed But Not Issued 1,280,267,228, Access Denied Tokens 96,298,507.
- 2025-03-31 supply categories in USDC: total supply 61,073,416,469, Tokens Allowed But Not Issued 996,628,065, Access Denied Tokens 101,016,689.

b02:s05 - PDF pages 1 and 2. The report observations are at 11:59 p.m. UTC. The report is dated April 30, 2025. Historical first-publication timing is unknown.
