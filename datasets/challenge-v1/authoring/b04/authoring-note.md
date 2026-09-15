# Private authoring note

## Sources, scope, and rights

The May report is retained as `ripple-rlusd-2025-05.pdf` with SHA-256 `93cf91ba21500f9580331ebe7eea5abc0719724343ebe9ede36a639ef585956e` and 514,953 bytes. Source URL: https://cdn.sanity.io/files/ior4a5y3/production/e5689456575be999b570160ec235451f3a77b221.pdf/Standard%20Custody%20and%20Trust%20LLC%20May%202025%20RLUSD%20Reserves%20Report%20-%20Issued.pdf. The June report is retained as `ripple-rlusd-2025-06.pdf` with SHA-256 `0741932e97423fc384eb5a22cb202330c27fbf3a211ba61e535ff9feac5f7135` and 580,828 bytes. Source URL: https://cdn.sanity.io/files/ior4a5y3/production/33ba3e71f1bd6c0dbb6601216fc05736eddf8879.pdf/Standard%20Custody%20%26%20Trust%20Company%2C%20LLC%20-%20RLUSD%20Reserves%20Report%20June%202025.pdf. Their local file modification times are 2026-10-06T22:14:45.025770Z and 2026-10-06T22:14:45.310135Z. Those are not original HTTP retrieval timestamps. The signed dates are June 23 and July 24, 2025. Historical publication times are unknown. The source PDFs are not redistributed. Only factual amounts, concise paraphrases, and stable page locators are retained.

## Independent Decimal calculations

May 30 reserve components total USD 322,099,766, reported circulating RLUSD is 309,043,794. June 30 reserve components total USD 471,227,699, reported reserve amount less the reconstruction is USD 0, with reported less reconstructed as the requested orientation. June 30 reported circulating RLUSD is 455,243,694.

Using each month's own reported circulating amount and reconstructed reserve components, June 30 coverage less May 30 coverage is -71.35472830422277781070659000 basis points. This month-end report-basis coverage decreased, so the proposition that it increased is contradicted. May and June observations use the same stated 5:00 p.m. Eastern cutoff. The earlier May 22 and June 9 observations remain in the data but are not part of the month-end comparison.

## Alternatives and plausible errors

An equivalent query can aggregate the three asset classes directly or unpivot them. The June 30 Treasury-bill dash is zero for reconstruction. The comparison must use May 30 with May 30 circulation and June 30 with June 30 circulation. Do not compare the early-period snapshots, apply a different circulation scope, use report-signing dates as data cutoffs, or describe a ratio change as a dollar reserve change. The statements describe report values and do not provide an independently observed market quote or redemption result.

## Synthetic controls

`june30_market_revaluation` increases June 30 money-market-fund value and the reported reserve amount by USD 1,000,000. The June component sum and coverage comparison change while the reconciliation stays zero.

`june30_component_gap` raises June 30 cash by USD 100 without changing the reported total. The component reconstruction changes by USD 100, the residual becomes negative USD 100 under report-minus-reconstruction orientation, and the coverage comparison changes.

`may30_market_revaluation` raises May 30 Treasury-bill fair value and its report total by USD 2,000,000. The residual remains zero, and the month-end coverage change moves while retaining its negative direction.

## Candidate-only shortcut audit

The request names three quantities and their units, identifies the two month-end observations, and defines the residual orientation. It gives no input column names or arithmetic expression. The candidate dictionary explains the report's scope and time basis without exposing calculated answers. The limited earlier observations are source-reported adjacent periods and remain distinct from month-end values.
## Accepted evidence paths

June 30 reconstructed reserves accept the June component schedule `b04:s04` alone, with `b04:s03` accepted as added period context. The reconciliation accepts the June report summary and component schedule `b04:s03` and `b04:s04`. Coverage and the bounded conclusion accept the matching May and June summary and component sections `b04:s01` through `b04:s04`. The two report definition sections `b04:s05` and `b04:s06` are also accepted when cited alongside those four sections.
