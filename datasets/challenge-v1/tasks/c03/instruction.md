For Block FY2024 versus FY2023, calculate bitcoin_gross_profit_2024_usd_thousand and bitcoin_gross_profit_2023_usd_thousand as Bitcoin revenue less matched Bitcoin costs, bitcoin_gross_profit_growth_pct, and bitcoin_share_of_total_net_revenue_increase_pct. Assess: Bitcoin revenue growth is a faithful proxy for Bitcoin gross-profit growth.

Task identifier: challenge-v1-c03.
Inputs are in /workspace: data.sqlite, evidence.json, sources.md, schema.json and check_answer.py.
Write one workpaper to /logs/artifacts/answer.json, following schema.json. Use exactly the requested claim IDs and units.
For each answered claim, supply a finite number and deterministic read-only SQLite returning one row and one numeric column. Any column alias is accepted.
Calculations must recompute on pristine original inputs and synthetic schema-compatible controls. Controls can change observations, reorder rows and change irrelevant periods. No hidden control values are supplied. Conclusions are scored on the original dossier only.
Cite the stable section IDs supporting each claim, including required definitions and period or population context. Equivalent source paths are accepted. Shared context_evidence may hold common definitions, while each claim must cite its own supporting facts. Do not cite unrelated sections.
Use insufficient_evidence with null value and null SQL for an unavailable requested quantity. Conclusion verdicts mean supported, contradicted, or not_established. Only the requested proposition is scored. Do not add factual prose outside the structured fields. Reason codes are optional and are not scored.
Per-claim absolute numerical tolerances in requested units:
- bitcoin_gross_profit_2024_usd_thousand: usd_thousand - 0.001
- bitcoin_gross_profit_2023_usd_thousand: usd_thousand - 0.001
- bitcoin_gross_profit_growth_pct: percent - 0.005
- bitcoin_share_of_total_net_revenue_increase_pct: percent - 0.005
Use the public structure checker: python /workspace/check_answer.py /logs/artifacts/answer.json. It checks delivery only and contains no financial answers. No live source acquisition is needed.


For unit matching, the grader trims surrounding whitespace, ignores case, and treats runs of ordinary whitespace or underscores as a single underscore. It does not convert units or scales.
