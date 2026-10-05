# Sources and redistribution

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
