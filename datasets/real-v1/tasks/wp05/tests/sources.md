# Export delivery note
This is an explicitly synthetic metric-migration case. Every period covers the same authored token/network population and complete event window. Amounts are whole token units with no valuation data.

First exclude mint and burn. largest_eligible_per_tx then retains the largest remaining event amount per transaction. all_eligible_events instead counts all remaining event amounts. The exports table states the definition used by each delivery. The requested comparable series is all_eligible_events. event_id is unique here.

The public Artemis July 2026 note motivates this scenario, but the rows, definitions and numbers are authored. These simplified definitions do not reconstruct Artemis labels, its full prior adjusted metric or a historical export. Methodology locator: https://www.artemis.ai/docs/data-reference/stablecoin-methodology
