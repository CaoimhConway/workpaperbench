For Microsoft FY2025, derive first-quarter consolidated results from the later release: report q1_revenue and q1_operating_income (USD million), and margin_change (Q2 minus Q1 consolidated GAAP operating margin, basis points). Compare Q2 Azure and other cloud services growth with the upper end of the constant-currency guidance issued October 30, 2024: report azure_gap (actual minus guidance upper end, percentage points). Assess: Q2 Azure constant-currency growth exceeded that upper end.

Task identifier: challenge-v1-a03.
Inputs are in /workspace: data.sqlite, evidence.json, sources.md, schema.json and check_answer.py.
Write one workpaper to /logs/artifacts/answer.json, following schema.json. Use exactly the requested claim IDs and units.
For each answered claim, supply a finite number and deterministic read-only SQLite returning one row and one numeric column. Any column alias is accepted.
Calculations must recompute on pristine original inputs and synthetic schema-compatible controls. Controls can change observations, reorder rows and change irrelevant periods. No hidden control values are supplied. Conclusions are scored on the original dossier only.
Cite the stable section IDs supporting each claim, including required definitions and period or population context. Equivalent source paths are accepted. Shared context_evidence may hold common definitions, while each claim must cite its own supporting facts. Do not cite unrelated sections.
Use insufficient_evidence with null value and null SQL for an unavailable requested quantity. Conclusion verdicts mean supported, contradicted, or not_established. Only the requested proposition is scored. Do not add factual prose outside the structured fields. Reason codes are optional and are not scored.
Per-claim absolute numerical tolerances in requested units:
- q1_revenue: usd_million - 0.0001
- q1_operating_income: usd_million - 0.0001
- margin_change: basis_points - 0.005
- azure_gap: percentage_points - 0.005
Use the public structure checker: python /workspace/check_answer.py /logs/artifacts/answer.json. It checks delivery only and contains no financial answers. No live source acquisition is needed.


For unit matching, the grader trims surrounding whitespace, ignores case, and treats runs of ordinary whitespace or underscores as a single underscore. It does not convert units or scales.
