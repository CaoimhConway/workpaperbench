# Sources and redistribution

## Active real-v1 snapshot

Six base tasks use authentic external numerical observations, normalized without changing their amounts. Two base tasks are deliberately synthetic. Real-task changed-input replay controls are deliberately perturbed real data. Diagnostic controls are fully synthetic. Neither counts as an observed base dataset.

| Task | Base provenance | Source group | Economic period or sample | Split |
|---|---|---|---|---|
| real-v1-wp01 | Deterministic source-derived filing facts | tesla-2024-q2 | Tesla calendar Q2/H1 2024 | Development |
| real-v1-wp02 | Fully synthetic event ledger, new equal-amount control | authored-event-ledger | Authored diagnostic | Development |
| real-v1-wp03 | Deterministic source-derived Bitcoin observations | bitcoin-halving-prefix | Block 840000, first 25 transactions | Evaluation |
| real-v1-wp04 | Deterministic source-derived issuer observations | circle-usdc-january-2025 | January 6 and January 31, 2025 at 23:59 UTC | Evaluation |
| real-v1-wp05 | Fully synthetic methodology migration | authored-migration | Authored diagnostic | Development |
| real-v1-wp06 | Deterministic source-derived Bitcoin observations | bitcoin-halving-prefix | Blocks 839999/840000, first 25 transactions each | Evaluation |
| real-v1-wp07 | Deterministic source-derived filing facts | apple-2024-q2 | Apple fiscal Q2/H1 FY2024 | Evaluation |
| real-v1-wp08 | Deterministic source-derived Bitcoin observations | bitcoin-halving-prefix | Block 840000, first 25 transactions | Evaluation |

Bitcoin supplies three tasks from one shared corpus. Circle supplies one crypto task. The two filing questions and migration diagnostic were previously exposed. The revised event task adds a new synthetic control to a previously exposed family. No source group crosses the development/evaluation split. This is not an independent-dataset or contamination-free study.

### Retained primary captures

[Capture metadata](datasets/real-v1/source-review.json) records access and rights decisions. [Bitcoin original responses and manifest](datasets/real-v1/captures/bitcoin-halving/bitcoin-halving.manifest.json) retain exact response bodies, request paths, SHA-256, retrieval time, units and fixed inclusion rules. [Circle factual extract](datasets/real-v1/captures/circle-usdc-jan2025.json) retains issuer facts, criteria paraphrases, PDF hash and date precision. [Tesla](datasets/real-v1/captures/tesla-filing-tables.json) and [Apple](datasets/real-v1/captures/apple-filing-tables.json) retain accession-specific table byte slices with full-document and extract hashes.

Blockstream's [Esplora specification pinned to a commit](https://github.com/Blockstream/esplora/blob/bb2d9f37bdb0eb0dade45b121a1df3581d7443ea/API.md) documents the actual API and its 25-transaction pagination. The source is factual Bitcoin public ledger data delivered by that service. The Esplora software license does not grant a blanket license to unrelated service content. The limited public-chain factual capture has attribution and is excluded from the project's MIT claims. There is no claimed provider endorsement or commercial data-service license.

The predetermined block pair spans the fourth subsidy halving. Both pages are partial: 25 of 2328 transactions in block 839999, and 25 of 3050 in block 840000. The captured noncoinbase population is the first 24 transactions after coinbase in each block. Selection occurred before model evaluation, based on the documented protocol boundary. Do not treat sampled fees as whole-block fees, outputs as payments, or two adjacent blocks as a causal or representative time-series result. Source block timestamps are April 20, 2024 at 00:05:33 and 00:09:27 UTC. Retrieval occurred October 6, 2026.

Circle's [January report](https://6778953.fs1.hubspotusercontent-na1.net/hubfs/6778953/USDCAttestationReports/2025/2025-USDC_Examination-Report-January-25.pdf) is an issuer report with an independent accountants opinion, not this project's own attestation. The report dates, signature/opinion date, HTTP Last-Modified header and retrieval are separate fields. Historical first publication time is unknown. The PDF is not bundled and no MIT license is claimed for it. Only limited attributed numerical facts and original explanatory annotations are retained. Circulation is a stock, reserves are USD fair value, and the report's par comparison does not provide market prices or transfer volume.

Issuer and SEC filing documents remain third-party material. Limited factual tables and locators are retained for offline reproduction, with no MIT claim over the original document. The two accession references are in the historical inventory below. Code and original annotations/synthetic diagnostics use [MIT](LICENSE).

### Sources inspected but not used

No `ARTEMIS_API_KEY` repository secret or supplied Artemis data credential was available. Current [API access documentation](https://www.artemis.ai/docs/artemis-api/api-key) says API access is plan-dependent. The unauthenticated catalog does not establish numerical entitlement. No paid plan, upgrade or private data integration was used.

DefiLlama's [current free specification](https://api-docs.defillama.com/llms-free.txt) and an actual fees response were inspected. Its [terms](https://defillama.com/terms) restrict copying/mirroring and republication of its data without permission. A code repository license is not a data redistribution grant. No DefiLlama numerical capture is bundled and no hypothetical provider integration is advertised. Coin Metrics' community archive has CC BY-NC 4.0 restrictions and was not needed.

The old PublicNode and Cloudflare failures remain in [their original record](sources/shared/capture_failure-37273047665.json). The third documented dRPC historical log path also failed with HTTP access errors, recorded in the new source review. Basic chain/header responses did not establish log access. Acquisition stopped at the bounded policy and adapted to a different real dataset. No synthetic fallback counts as an observed source here.

## Historical v1 snapshot

Original code, annotations and synthetic fixtures use MIT. Issuer filings and
third-party methodology remain with their owners. Full documents are not bundled.
Each evidence record supplies a locator or synthetic origin, publication precision,
economic period, retrieval timestamp, content/table hashes and redistribution
decision. Inputs run offline after acquisition.

| Task | Split | Origin | Source group | Source and context |
|---|---|---|---|---|
| wp01 | Development | Primary filing facts | tesla-2024-q2 | [Tesla 10-Q](https://www.sec.gov/Archives/edgar/data/1318605/000162828024032662/tsla-20240630.htm), filed July 24, 2024. Three- and six-month June 30 R&D columns in USD million. |
| wp02 | Development | Original synthetic ledger | authored-event-ledger | Copied export rows, distinct event identity and explicit mint/burn labels. No observed transactions. |
| wp03 | Evaluation | Original synthetic releases | authored-dated-releases | Day-level publication dates and same Ethereum USDC population. Latest release by July 5, 2024 is eligible. No USD valuation input. |
| wp04 | Evaluation | Synthetic acquisition downgrade | synthetic-usdc-window | Fixed chain-1 window 20,000,000-20,000,031, authored symbolic event/transaction/participant labels and amounts. Shared with wp08. |
| wp05 | Development | Original synthetic migration | authored-migration | Original rows and delivery definitions. [Artemis July 2026 methodology](https://www.artemis.ai/docs/data-reference/stablecoin-methodology) motivates the question and supplies none of the numbers or labels. |
| wp06 | Evaluation | Original synthetic coverage case | synthetic-coverage-expansion | Authored network/asset populations and one-to-many metadata tags. No observed feed history. |
| wp07 | Evaluation | Primary filing facts | apple-2024-q2 | [Apple 10-Q](https://www.sec.gov/Archives/edgar/data/320193/000032019324000069/aapl-20240330.htm), filed May 3, 2024. Fiscal Q2 and six months ended March 30 Services sales and gross profit in USD million. |
| wp08 | Evaluation | Synthetic acquisition downgrade | synthetic-usdc-window | Identical original corpus to wp04, with explicitly absent business-purpose and account-to-person labels. |

The two shared tasks are one dataset. Related conceptual families and repetitions
are not independent datasets. Synthetic actor labels are authored facts, without
wallet attribution.

The bounded capture ran on Actions
[37273047665](https://github.com/CaoimhConway/workpaperbench/actions/runs/37273047665).
[PublicNode](https://ethereum.publicnode.com/) returned an HTTPError and the
[documented Cloudflare gateway](https://developers.cloudflare.com/web3/ethereum-gateway/reference/supported-networks/)
returned an RPC error. Each path made one bounded request for the fixed window.
The preserved [failure record](sources/shared/capture_failure-37273047665.json)
contains the actual classes and request counts. There were no further providers,
windows or cherry-picking. The authorized synthetic fallback is materially weaker
than observed logs and supports no empirical claim about chain activity.

The shared fixture uses [Circle's Ethereum USDC address](https://developers.circle.com/stablecoins/usdc-contract-addresses)
and the six-decimal configuration from [Circle's source example](https://github.com/circlefin/stablecoin-evm/blob/master/.env.example).
Its symbolic block/transaction identities and all amounts are original synthetic
data. The acquisition validator uses the [ERC-20 Transfer event](https://eips.ethereum.org/EIPS/eip-20),
[Solidity event ABI](https://docs.soliditylang.org/en/latest/abi-spec.html#events)
and [Ethereum getLogs protocol](https://ethereum.org/developers/docs/apis/json-rpc/#eth_getlogs).
No successful ABI or contract metadata capture is claimed. Token units are not a
supplied USD valuation.

Artemis's note documents changing transfer-volume semantics and distinct delivery
surfaces. It does not establish a product bug or historical series discontinuity.
The simplified largest-eligible-event-per-transaction definition omits prior
adjustments and proprietary classifications. It does not reproduce the full
Artemis-adjusted metric. No endorsement is implied.

Every changed-data database is an explicit synthetic recomputation control,
including for filing tasks. It varies amounts without changing schema, definitions,
coverage or eligibility. References are authored outputs, distinct from actual
saved submissions. Review records and independently recalculated values appear in
[reports/source-review.md](reports/source-review.md). No external human validation
is claimed. Dependency notices are in [third-party/NOTICE.md](third-party/NOTICE.md).


## Research Challenge snapshot

The `challenge-v1` pilots retain authentic numerical facts from accession-specific Adobe Q3/Q4 FY2024 releases, PayPal FY2024 filing and earnings supplement, and Brale SBC May/June 2025 issuer reserve reports. Their exact URLs, source sections, capture time, original-response hashes where available and retained-extract hashes are in each `datasets/challenge-v1/authoring/*/source_capture.json`. Full issuer HTML/PDF documents are not redistributed. Retained material is factual table amounts, headings and concise definitions with attribution. Code and original annotations are MIT, while issuer source rights are not relicensed as project code. No benchmark questions are copied.

Brale PDF bytes were read through the PDF reader but not captured locally, so only retained-extract hashes are claimed. Printed examiner/management dates are report dates, and historical first publication remains unknown. Both dates are month-end stocks. May and June list the same chains and reserve definition but have different examiner scope. No daily flow, token market price, observed redemption outcome or payment population is inferred. Synthetic controls are labeled and never described as authentic financial observations.

Artemis acquisition is skipped because no explicitly supplied project data credential or verified redistribution grant exists. The prior RPC and DefiLlama failures/rights limitations remain historical. This snapshot uses direct primary issuer evidence instead of repeating those failed acquisition paths.

### Separate evaluation source groups

Nine evaluation cases use nine issuer/source-window groups, separate from all three development groups. Five evaluation cases concern actual crypto or stablecoin economic observations. With Brale development, six of the twelve challenge cases meet that scope. These are disclosure-based financial measurements, not a claim to identify on-chain business payments.

| Case | Primary group | Economic scope | Research decision |
|---|---|---|---|
| a02 | NVIDIA FY2025 Q2/Q3 releases | Prior August 2024 guidance and October 27 actual quarter | Rebuild signed non-GAAP gross profit and compare revenue/margin with prior upper guidance |
| a03 | Microsoft FY2025 Q1/Q2 disclosures | October 2024 guidance and December 31 quarter/half-year | Derive Q1 from Q2 and half-year, then compare margins and constant-currency Azure guidance |
| a04 | Oracle FY2025 Q1/Q2 releases | September 2024 guidance and November 30 actual quarter | Reconcile expected currency impact and after-tax non-GAAP adjustments |
| b02 | Circle USDC March 2025 reserve report | March 19 and March 31, 23:59 UTC stocks | Independently derive circulation and reserve assets, then reconcile coverage |
| b03 | Tether June 2025 detailed report and July release | June 30, 23:59 UTC stocks | Rebuild reserve components and net token liabilities, distinguish company scope and cross-publication amounts |
| b04 | Ripple RLUSD May/June 2025 reserve reports | May 30 and June 30, 17:00 Eastern stocks | Derive asset totals and an oriented residual, compare report-basis coverage |
| c02 | Coinbase FY2024 filing and letter | Annual revenue and rounded spot trading volume, FY2023 recast comparator | Separate proxy arithmetic from comparable fee-rate inference and unavailable business-payment counts |
| c03 | Block FY2024 filing | Original annual Bitcoin revenue and costs with FY2023 comparator | Distinguish gross revenue growth from gross profit and contribution to consolidated revenue change |
| c04 | Visa FY2024 filing and release | September-ended revenue and its disclosed June-ended payment-volume window | Match lagged population/timing and assess limits of aggregate pricing attribution |

Each authoring directory retains source URLs, section/page locators, authentic capture hashes, extract hashes and date precision. Historical HTML/PDF documents are local acquisition material and excluded from published packages. The PDF file timestamps available for Circle, Tether and Ripple are local retention metadata, not original server retrieval times. Unknown PDF publication times stay unknown. Report signatures, release publication dates, economic cutoffs and retrieval times remain separate. Tether's release additionally has actual bounded HTTP retrieval metadata. Rounded Coinbase spot volume is used at the disclosed whole-billion precision.

The SEC supplies several issuers, so shared delivery infrastructure and filing templates are provider/template overlap rather than extra independent datasets. Circle's evaluation issuer also appears in Core Regression at a different January window. No challenge development issuer/source-window group crosses the evaluation split. Synthetic changed-input controls and repetitions add no base cases. No claim of contamination-free web history or issuer-independent statistical inference is made.
