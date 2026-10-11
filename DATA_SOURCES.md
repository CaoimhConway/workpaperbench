# Sources and redistribution

The default `workflow-v8` catalog contains 30 source-backed financial tasks:
six development cases and 24 evaluation cases. Each dossier supplies attributed
source excerpts, normalized observations, definitions and an output contract.
The maintenance catalog, `workflow-v7`, uses the same financial source groups.
See [workflow methods](docs/WORKFLOW.md) for the split, measurement contract and
limits of the supplied evidence.

## Source provenance

Issuer filings, earnings releases and reserve reports supply the base financial
observations. Each authoring directory under
[`datasets/challenge-v1/authoring`](datasets/challenge-v1/authoring) retains source
URLs, section or page locators, publication precision, economic periods and
capture or extract hashes. The expanded workflow source bindings are recorded in
[`reports/local/workflow-source-review.json`](reports/local/workflow-source-review.json).
Full issuer HTML and PDF documents are not redistributed.

The three development source groups are Microsoft fiscal disclosures, Brale
stablecoin reserve reports and Block annual disclosures. No issuer/source-window
group crosses the development/evaluation split. Shared SEC delivery infrastructure,
issuer templates and related economic questions remain overlap. Published
references and public source history preclude a contamination-free evaluation claim.

Original source facts, authored annotations, reference workpapers and synthetic
controls have distinct provenance. Controls deliberately change inputs to test
recomputation. They are not additional observed financial datasets. Report
signatures, release publication dates, economic cutoffs and retrieval times remain
separate. Unknown historical publication times stay unknown. A retained-extract
hash identifies the extract, not an uncaptured original PDF.

## Rights and reuse

WorkpaperBench code, original annotations, schemas and synthetic fixtures use
[MIT](LICENSE). Issuer documents and third-party factual captures remain their
owners' material and are excluded from that license claim. Retained excerpts are
limited to attributed factual tables, headings and concise definitions needed
for offline reproduction. No endorsement or blanket data-service redistribution
license is claimed. Dependency notices are in
[`third-party/NOTICE.md`](third-party/NOTICE.md).

## Historical collections

Historical catalogs keep separate experiment and scoring identities. Their
scores are not construction-track results.

| Collection | Base observations | Important limits |
| --- | --- | --- |
| Original eight-task study | Tesla and Apple filing facts plus six authored synthetic cases | Two tasks share one synthetic token-transfer corpus. Synthetic event identities, amounts and actor labels are not observed chain activity. |
| `real-v1` | Six tasks derived from Tesla, Apple, Circle and Bitcoin observations, plus two synthetic diagnostics | Three Bitcoin tasks share one sampled corpus. Previously exposed questions are regression cases. |
| Research Challenge | Accession-specific issuer releases, filings and stablecoin reserve reports | Source groups, report cutoffs and scope differ. Reserve stocks do not establish payment flows or redemption outcomes. |

The filing sources include
[Tesla's June 2024 10-Q](https://www.sec.gov/Archives/edgar/data/1318605/000162828024032662/tsla-20240630.htm)
and [Apple's March 2024 10-Q](https://www.sec.gov/Archives/edgar/data/320193/000032019324000069/aapl-20240330.htm).
The migration and event-ledger cases are authored diagnostics with explicit
delivery definitions. They reproduce no proprietary adjusted metric.

### Bitcoin sampling

The [retained capture manifest](datasets/real-v1/captures/bitcoin-halving/bitcoin-halving.manifest.json)
binds exact public-ledger response bodies, request paths, hashes, units and fixed
inclusion rules. The pinned [Esplora API specification](https://github.com/Blockstream/esplora/blob/bb2d9f37bdb0eb0dade45b121a1df3581d7443ea/API.md)
documents 25-transaction pagination. The capture includes the first 25 of 2328
transactions in block 839999 and the first 25 of 3050 in block 840000, spanning
the fourth subsidy halving. Noncoinbase analysis uses the first 24 transactions
after coinbase in each page.

These samples are not whole-block totals or representative time series. Outputs
are not identified business payments. Matching transaction versions across pages
does not match individual transactions or prove instrumentation changes. The
limited factual capture has attribution and is excluded from the project's MIT
claim. A software license does not license unrelated service content.

### Reserve observations

[Circle's January 2025 report](https://6778953.fs1.hubspotusercontent-na1.net/hubfs/6778953/USDCAttestationReports/2025/2025-USDC_Examination-Report-January-25.pdf)
supplies dated circulation and USD fair-value reserve stocks.
The [factual extract](datasets/real-v1/captures/circle-usdc-jan2025.json) retains
the PDF hash, numerical facts and date precision. The PDF is not bundled.
The issuer report includes an independent accountants opinion. WorkpaperBench
does not perform an attestation. A par comparison supplies neither token market
prices nor transfer volume.

The Challenge reserve dossiers similarly retain report-basis definitions and
dated stocks. Different examiner scopes and observation times constrain
comparisons. No daily flow, business-payment population or observed redemption
outcome is inferred from these reports.

## Historical publication copies

Historical task copies contain neutral context descriptions. The explicit
[`publication-inputs.json`](config/publication-inputs.json) registry binds them
to original manifest hashes and separate publication hashes. Financial tables,
reference answers, evidence IDs, controls and grading contracts remain fixed.
Exact original files are retained locally. Publication projections are not new
model trials and cannot relaunch an old paid campaign under its original freeze.
