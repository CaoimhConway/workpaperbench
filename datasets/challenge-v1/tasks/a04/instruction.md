For Oracle Q2 FY2025, independently rebuild guidance_upper (the prior non-GAAP diluted EPS guidance upper end including its disclosed expected favorable currency impact, USD per share) and report eps_gap (actual reported non-GAAP diluted EPS minus that target, USD per share). Rebuild net_income_adjustment (after-tax non-GAAP adjustment, USD million) and adjusted_net_income (USD million) from the quarter GAAP result and disclosed expense and tax adjustments, then report adjusted_net_margin (percent). Assess: reported Q2 non-GAAP diluted EPS exceeded the prior upper target including the expected currency impact.

Task identifier: challenge-v1-a04.
Inputs are in /workspace: data.sqlite, evidence.json, sources.md, schema.json and check_answer.py.
Write one workpaper to /logs/artifacts/answer.json, following schema.json. Use exactly the requested claim IDs and units.
For each answered claim, supply a finite number and deterministic read-only SQLite returning one row and one numeric column. Any column alias is accepted.
Calculations must recompute on pristine original inputs and synthetic schema-compatible controls. Controls can change observations, reorder rows and change irrelevant periods. No hidden control values are supplied. Conclusions are scored on the original dossier only.
Cite the stable section IDs supporting each claim, including required definitions and period or population context. Equivalent source paths are accepted. Shared context_evidence may hold common definitions, while each claim must cite its own supporting facts. Do not cite unrelated sections.
Use insufficient_evidence with null value and null SQL for an unavailable requested quantity. Conclusion verdicts mean supported, contradicted, or not_established. Only the requested proposition is scored. Do not add factual prose outside the structured fields. Reason codes are optional and are not scored.
Per-claim absolute numerical tolerances in requested units:
- guidance_upper: usd_per_share - 0.0001
- eps_gap: usd_per_share - 0.0001
- net_income_adjustment: usd_million - 0.0001
- adjusted_net_income: usd_million - 0.0001
- adjusted_net_margin: percent - 0.005
Use the public structure checker: python /workspace/check_answer.py /logs/artifacts/answer.json. It checks delivery only and contains no financial answers. No live source acquisition is needed.


For unit matching, the grader trims surrounding whitespace, ignores case, and treats runs of ordinary whitespace or underscores as a single underscore. It does not convert units or scales.
