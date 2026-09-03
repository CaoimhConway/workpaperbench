# Export delivery note
This is an explicitly synthetic metric-migration case. Every period covers the same authored token/network population and complete event window. Amounts are whole token units with no valuation data.

First exclude mint and burn. largest_eligible_per_tx then retains the largest remaining event amount per transaction. all_eligible_events instead counts all remaining event amounts. The exports table states the definition used by each delivery. The requested comparable series is all_eligible_events. event_id is unique here.

The rows, delivery definitions and numbers are authored. These simplified definitions reproduce neither a proprietary adjusted metric nor a historical export.
