# Private authoring note

## Source choice and rights

First Digital Labs' official page lists paired May and June reports, but both PDFs were hosted on a CDN the browser safety policy blocked. Direct command-line retrieval also failed at DNS resolution. After that bounded attempt, this dossier uses the two issuer-hosted Brale reports. Brale is distinct from Circle, Tether and Paxos. The web PDF reader exposed the complete two-page text for each report with page locators. The source PDFs were not downloaded, and their full contents are not redistributed. `source-extracts.md` retains source facts and concise paraphrases only.

The reports' exact URLs and access times are in `source_capture.json`. No byte hash is asserted for either source PDF. The retained extract receives its own content hash after authoring. Their printed June 12 and July 16 dates are report/signature dates. Historical first-publication timestamps are unknown.

## Independent calculations

All source amounts are whole U.S. dollars and all issued figures are SBC units.

- May component reconstruction: 2,210,784 + 4,883,011 = 7,093,795 USD. The reported asset total and reported issue count are each 7,093,795.
- June component reconstruction: 3,475,633 + 5,880,883 = 9,356,516 USD. The reported asset total and reported issue count are each 9,356,516.
- May report-convention coverage: 100 × 7,093,795 / 7,093,795 = 100 percent.
- June report-convention coverage: 100 × 9,356,516 / 9,356,516 = 100 percent.
- June minus May coverage: 0 percentage points. The proposition that the reported coverage increased is contradicted by the calculation.

These reference values were recomputed from the retained source facts using `Decimal`, independently of any task SQL.

## Metric and comparison limits

The report's issued amount is total supply on its supported blockchains at the report date. Its reserve definition is the total balance of U.S.-denominated assets in unencumbered accounts segregated from other Brale accounts. The task coverage calculation follows the report's own comparison of fair-value USD to issued SBC units. It is a report-basis ratio, not a secondary-market price, independently observed redemption result, liquidation estimate, or proof about each token holder.

Both data cutoffs are month-end at 11:50 p.m. Eastern Time. The report preparation/signature dates are later, on June 12 and July 16 respectively, and are not data cutoffs. The tables and stated reserve definition align across periods. Examiner identity and described scope do not: May is an Abdo independent accountant report under AICPA attestation standards. June is a Michael Coglianese, CPA, P.C. performance attestation that says it relied on company-provided data and was not retained to independently confirm data authenticity or accuracy. A comparison of the published amounts must not be described as equal assurance or independent validation of each underlying record.

## Legitimate alternatives and plausible errors

- A valid query may sum the two June component columns directly. Another valid query may unpivot the two component rows and aggregate them. For coverage, either explicitly calculate both report-date ratios or compare reported assets and issued supply within each report before taking the difference.
- A plausible wrong calculation uses the change in USD reserve assets as the change in coverage. Coverage is a ratio to issued SBC, not a dollar change in the numerator alone.
- A plausible wrong comparison divides June assets by May issuance or uses May assets against June issuance. These are different reporting dates.
- Using June 30 as the signature date, or July 16 as the measurement cutoff, confuses the economic observation date with publication/signature timing.
- Adding reported issued supplies across chain names would double-count the report total. The table already defines issued amount as total supply across supported blockchains.
- Reconstructing the June components to equal the disclosed total does not independently establish their valuation. It is an arithmetic reconciliation of the published fields.

## Control calculations

`changed_tables` increases June cash and the disclosed total by USD 200,000, leaving issued SBC unchanged. The June components then sum to USD 9,556,516, reconciliation remains USD 0, and coverage change is 2.137547779536742 percentage points. This makes the stated increase proposition supported.

The `component_gap` control raises June cash by USD 1 without changing the disclosed total or issued amount. Component-derived assets become USD 9,356,517, reconciliation becomes USD 1, and coverage change remains zero. This control separates component reconstruction and reconciliation from the coverage comparison.


## Candidate-only shortcut audit and retained scope

The candidate instruction names three claim IDs, their units, the two observation periods, and one narrow proposition. It does not expose the source column names, calculation formula, expected values, or expected verdict. Candidate context states the report definitions and the source's examination limits without reproducing calculated answers.

The retained reports provide aggregate cash and cash-equivalent amounts, aggregate U.S. government backed debt, total issued supply across the listed supported chains, the issuer's reserve-value definition, observation timing, and examiner scope. They do not provide security-level holdings, maturity or yield detail, network-specific issuance subtotals, a contemporaneous secondary-market price, or evidence of a realized redemption. The documents' publication timestamps remain unknown. June's examiner expressly relies on company-provided data and does not independently confirm its authenticity or accuracy.
