For NVIDIA Q3 FY2025, compare actual revenue with the upper end of guidance issued August 28, 2024, and independently rebuild non-GAAP gross profit from GAAP gross profit and the signed gross-profit adjustments. Report revenue_gap (actual minus prior guidance upper end, USD million), adjusted_gross_profit (USD million), adjusted_gross_margin (percent using the rebuilt amounts), and margin_gap (rebuilt margin minus prior non-GAAP guidance upper end, basis points). Use displayed dollar amounts for the margin calculation. Assess: the rebuilt Q3 non-GAAP gross margin exceeded the upper end of that prior guidance.

Task identifier: challenge-v1-a02.
Inputs are in /workspace: data.sqlite, evidence.json, sources.md, schema.json and check_answer.py.
Write one workpaper to /logs/artifacts/answer.json, following schema.json. Use exactly the requested claim IDs and units.
For each answered claim, supply a finite number and deterministic read-only SQLite returning one row and one numeric column. Any column alias is accepted.
Calculations must recompute on pristine original inputs and synthetic schema-compatible controls. Controls can change observations, reorder rows and change irrelevant periods. No hidden control values are supplied. Conclusions are scored on the original dossier only.
Cite the stable section IDs supporting each claim, including required definitions and period or population context. Equivalent source paths are accepted. Shared context_evidence may hold common definitions, while each claim must cite its own supporting facts. Do not cite unrelated sections.
Use insufficient_evidence with null value and null SQL for an unavailable requested quantity. Conclusion verdicts mean supported, contradicted, or not_established. Only the requested proposition is scored. Do not add factual prose outside the structured fields. Reason codes are optional and are not scored.
Per-claim absolute numerical tolerances in requested units:
- revenue_gap: usd_million - 0.0001
- adjusted_gross_profit: usd_million - 0.0001
- adjusted_gross_margin: percent - 0.005
- margin_gap: basis_points - 0.005
Use the public structure checker: python /workspace/check_answer.py /logs/artifacts/answer.json. It checks delivery only and contains no financial answers. No live source acquisition is needed.


For unit matching, the grader trims surrounding whitespace, ignores case, and treats runs of ordinary whitespace or underscores as a single underscore. It does not convert units or scales.
