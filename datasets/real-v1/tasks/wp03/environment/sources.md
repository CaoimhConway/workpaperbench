# Bitcoin capture dictionary
Two Bitcoin Mainnet blocks, 839999 and 840000, selected at the protocol's fourth subsidy halving before values or model outcomes were inspected. Each observed API page contains transaction indices 0 through 24, including the coinbase. This is complete only for that fixed prefix sample. The full blocks contain more transactions. Missing later pages are not zero fees or an instrumentation change.

Values and fees are integer satoshis. One BTC is 100000000 satoshis. Transaction fee is input prevout values minus output values. The virtual size is ceiling(weight / 4), in virtual bytes. A sample aggregate fee rate is sum(noncoinbase fees) / sum(noncoinbase virtual sizes), not the mean of transaction fee-rate scalars. Output amounts include change and cannot be classified as payments here.

version is the transaction's actual consensus serialization version. Matched-version coverage keeps only versions present in both noncoinbase prefix samples, using this same sampling rule. It does not match individual transactions or people and makes no representative-population claim.

The subsidy rule is 5000000000 satoshis right-shifted by floor(height / 210000). Coinbase outputs are claimed compensation, not transaction fees or miner profit. Payout minus the nominal subsidy is called claimed compensation above subsidy. It is not asserted to equal all fees in the block since compensation may be unclaimed. The prefix fees never establish the full-block total.

The captures establish neither business purpose nor account-to-person mappings. A transaction can contain multiple outputs, including change and zero-value outputs. Summed outputs are not payment adoption, unique people or economic growth. The two adjacent blocks cannot establish a causal effect of the halving.

Original observations were retrieved in 2026. Block timestamps are consensus source fields, distinct from retrieval, and do not establish a vendor's historical publication time. Native changed-input controls are explicitly synthetic and alter amounts while preserving schema, sampling and definitions.

Primary API specification: https://github.com/Blockstream/esplora/blob/bb2d9f37bdb0eb0dade45b121a1df3581d7443ea/API.md
Subsidy implementation: https://github.com/bitcoin/bitcoin/blob/v27.0/src/validation.cpp
