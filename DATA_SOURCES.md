# Sources and redistribution

Only original code, annotations, synthetic fixtures and concise factual extracts are licensed under MIT. Original issuer filings and third-party methodology text remain with their owners. Full filings are not bundled. `evidence.json` records publication precision, economic period, retrieval timestamp, content hash, derived table hash and redistribution decision. Inputs run offline after acquisition.

| Task | Origin | Source group | Locator and context |
|---|---|---|---|
| wp01 | Primary filing facts | tesla-2024-q2 | [Tesla 10-Q](https://www.sec.gov/Archives/edgar/data/1318605/000162828024032662/tsla-20240630.htm), filed 2024-07-24. R&D table in USD millions with separate three-month and six-month June 30 columns. |
| wp02 | Original synthetic ledger | authored-event-ledger | Original event identities, copied export rows and explicit mint/burn labels. No observed transactions or wallet attribution. |
| wp05 | Development | Original synthetic migration | authored-migration | Authored rows and delivery definitions. No observed export history. |

The source review independently recalculated Tesla Q1 R&D as 2,225 minus 1,074 = 1,151 USD million, and sequential change as (1,074 minus 1,151) / 1,151 times 100 = -6.689834926%. It checked period headers, entity and units. This is source review, not external human validation.

Every `changed.sqlite` is an explicitly synthetic schema-compatible SQL recomputation control. It changes amounts even when the original task uses a real filing or observed capture. Changed-control data never inherit the real-source provenance label.

Reference JSON workpapers are authored expected outputs. They are separate from model submissions. All source review is recorded without claims of endorsement or independent human validation.
