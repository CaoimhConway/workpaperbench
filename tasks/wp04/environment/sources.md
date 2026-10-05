# Shared USDC window fixture
This is an explicitly synthetic downgrade after both bounded public-RPC acquisition paths failed in Actions run 37273047665. It contains original authored events, symbolic block/transaction identifiers and participant labels. It is not an observed chain capture. Both tasks reuse this same source group.

The scenario covers chain 1, blocks 20000000 through 20000031 inclusive, and the Ethereum USDC contract 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48. Amounts are integer base units. The supplied decimal scale is 6, so token-unit amounts scale by 1000000. No dollar valuation is provided.

Event identity is (chain_id, block_id, log_index). Each listed event is unique. A transaction may contain several distinct events. First exclude events whose sender or recipient is the zero address 0x0000000000000000000000000000000000000000. These represent mint/burn in this fixture. all_events then sums all remaining event amounts. max_per_tx retains only the largest remaining event amount in each transaction. Both aggregates cover the same window. They are two counting definitions, not two temporal observations. max_per_tx does not reproduce the full prior Artemis-adjusted metric or its proprietary labels.

The delivered columns are event identity, block number, transaction, symbolic sender/recipient and amount. There are no other time windows, business-purpose classifications, actor/entity-type labels or links from accounts to natural persons. Participants are symbolic account labels, without wallet attribution.

Primary metadata/definition locators: https://developers.circle.com/stablecoins/usdc-contract-addresses and https://eips.ethereum.org/EIPS/eip-20 . Public methodology motivation only: https://www.artemis.ai/docs/data-reference/stablecoin-methodology . All fixture amounts, identities and labels are original synthetic data. Changed controls are also synthetic.

