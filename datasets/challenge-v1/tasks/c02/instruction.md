For Coinbase FY2024 versus FY2023, report transaction_revenue_growth_pct and spot_trading_volume_growth_pct as percentages, transaction_revenue_to_spot_volume_proxy_2024_pct as a percentage, and proxy_change_bps as FY2024 minus FY2023 basis points. Also report business_payment_count_2024, the count of payments between businesses processed through Coinbase in FY2024, in count units. Use displayed source values and the FY2023 revenue categories presented in the FY2024 filing. Assess: the annual transaction-revenue-to-Trading-Volume ratio is a comparable realized spot trading fee rate across the two years.

Task identifier: challenge-v1-c02.
Inputs are in /workspace: data.sqlite, evidence.json, sources.md, schema.json and check_answer.py.
Write one workpaper to /logs/artifacts/answer.json, following schema.json. Use exactly the requested claim IDs and units.
For each answered claim, supply a finite number and deterministic read-only SQLite returning one row and one numeric column. Any column alias is accepted.
Calculations must recompute on pristine original inputs and synthetic schema-compatible controls. Controls can change observations, reorder rows and change irrelevant periods. No hidden control values are supplied. Conclusions are scored on the original dossier only.
Cite the stable section IDs supporting each claim, including required definitions and period or population context. Equivalent source paths are accepted. Shared context_evidence may hold common definitions, while each claim must cite its own supporting facts. Do not cite unrelated sections.
Use insufficient_evidence with null value and null SQL for an unavailable requested quantity. Conclusion verdicts mean supported, contradicted, or not_established. Only the requested proposition is scored. Do not add factual prose outside the structured fields. Reason codes are optional and are not scored.
Per-claim absolute numerical tolerances in requested units:
- transaction_revenue_growth_pct: percent - 0.005
- spot_trading_volume_growth_pct: percent - 0.005
- transaction_revenue_to_spot_volume_proxy_2024_pct: percent - 0.005
- proxy_change_bps: basis_points - 0.005
- business_payment_count_2024: count - 0
Use the public structure checker: python /workspace/check_answer.py /logs/artifacts/answer.json. It checks delivery only and contains no financial answers. No live source acquisition is needed.


For unit matching, the grader trims surrounding whitespace, ignores case, and treats runs of ordinary whitespace or underscores as a single underscore. It does not convert units or scales.
