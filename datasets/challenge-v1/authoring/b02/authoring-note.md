# Private authoring note

## Source, scope, and rights

The issuer-hosted March 2025 USDC examination report is retained locally as `circle-usdc-2025-03.pdf`. Original source: https://6778953.fs1.hubspotusercontent-na1.net/hubfs/6778953/USDCAttestationReports/2025/2025%20USDC_Examination%20Report%20March%2025.pdf. Local bytes are 280,094 with SHA-256 `541977454bab0529808c91016082d25ec6460d89269b225b0c347bc768aefe81`. Its local file modification time is 2026-10-06T22:14:43.906234Z. That local timestamp is not an original HTTP retrieval timestamp. The printed April 30, 2025 date is a report/signature date. Historical publication time is unknown. Only concise facts and locators are retained, not the report PDF.

## Independent Decimal reconstruction

The source lists March 19 and March 31 observations at 11:59 p.m. UTC. The March 19 line items sum to USD 59,147,592,128. The March 31 line items sum to USD 60,040,707,041. For March 31, total supply less both source-defined exclusions is 59,975,771,715 USDC. At displayed whole-dollar precision, the March 31 line items sum to USD 1 more than the source-reported reserve total, so report minus reconstruction is USD -1.

For the coverage comparison, March 19 reserve components divided by March 19 source-defined circulation and March 31 components divided by March 31 circulation give a March 31 minus March 19 change of -0.157597619765173756604460000 basis points. Coverage is above 100% on both source dates. The reserve total is fair value under the report's definition, not a market price, realized redemption, liquidation value, or independent validation of each underlying holding.

## Alternatives and plausible errors

A valid reconstruction can aggregate the CUSIP rows with the other reserve lines, or use an equivalent unpivoted line-item structure. Signed timing adjustments remain negative. Circulation can be computed with conditional aggregation or by summing gross supply and subtracting the two excluded categories. For coverage, compare each observation using its own circulation and reserve balance. Do not use the report signature date as an observation date, combine balances across dates, add CUSIP subtotal lines to the CUSIP detail, or use the change in reserve dollars as a coverage change. The reported circulation and reserve values are report-defined measurements. A component reconciliation is arithmetic, not independent verification of valuation or custody.

## Synthetic controls

`march31_treasury_revaluation` raises one March 31 security fair value and the reported March 31 reserve total by USD 30 million. The component total changes by the same amount, the residual remains USD -1, and the coverage change moves while both-date coverage stays above 100%.

`march31_supply_change` increases the March 31 gross supply by 1 million USDC. No observation date or reserve line changes. March 31 derived circulation and coverage change.

`march31_component_gap` raises March 31 segregated-bank cash by USD 5,000 without changing the reported total. The reconstructed reserve assets and coverage change, and the report-minus-reconstruction residual becomes negative USD 5,001.

## Candidate-only shortcut audit

The request names only four claim IDs and their units, states both observation dates, and defines the residual direction. It provides no table column names, arithmetic template for aggregation, precomputed reconstruction, or expected answer. The source-defined circulation criteria are included in the dictionary because they define the measured quantity. The retained excerpts include the issuer's report totals only where a reconciliation requires them.
## Accepted evidence paths

The minimal circulation citation is `b02:s04`. The matching definition section `b02:s01` is also accepted alongside it. March 31 reconstruction and residual claims accept `b02:s03` alone, with `b02:s05` accepted as added cutoff context. Coverage accepts the March 19 and March 31 component schedules plus supply inputs `b02:s02`, `b02:s03` and `b02:s04`. The reserve-criteria section `b02:s01` is accepted as added scope context.
