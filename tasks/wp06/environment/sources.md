# Observation dictionary and feed notes

This is an explicitly synthetic coverage-expansion case. Each row in `observations` is an amount in whole token units for one `network_asset` key in one period. The key identifies a network and asset together. There is one observation per key and period. No USD valuation input is supplied.

A reported period total is the sum of every observation row in that period. Matched coverage is the intersection of `network_asset` keys present in both P1 and P2. For matched growth, sum observations for those same keys in each period. Keys newly observed in only one period remain in the reported total and are not part of the matched-coverage total.

`asset_tags` is a one-to-many metadata catalog. Its tags describe asset context and do not define the measurement population or amount. `published_on` dates when a synthetic tag entry was published, not the economic observation period. Use `observations` and the coverage definition for the calculations.

