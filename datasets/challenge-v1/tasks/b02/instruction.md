Using the Circle March 2025 reserve report, independently reconstruct `march31_reserves_usd` (USD) from the March 31 reserve line items, including the signed timing and settlement adjustments. Independently derive `march31_circulation_usdc` (USDC) from the March 31 supply and exclusion categories. Report `march31_residual_usd` (USD), oriented as the report-stated reserve amount less your component reconstruction. Report `coverage_change_bps` (basis_points) as March 31 coverage minus March 19 coverage, using each date’s reconstructed reserve assets and source-defined circulation. Assess whether coverage exceeded 100% at both dates.

Task identifier: challenge-v1-b02.
Inputs are in /workspace: data.sqlite, evidence.json, sources.md, schema.json and check_answer.py.
Write one workpaper to /logs/artifacts/answer.json, following schema.json. Use exactly the requested claim IDs and units.
For each answered claim, supply a finite number and deterministic read-only SQLite returning one row and one numeric column. Any column alias is accepted.
Calculations must recompute on pristine original inputs and synthetic schema-compatible controls. Controls can change observations, reorder rows and change irrelevant periods. No hidden control values are supplied. Conclusions are scored on the original dossier only.
Cite the stable section IDs supporting each claim, including required definitions and period or population context. Equivalent source paths are accepted. Shared context_evidence may hold common definitions, while each claim must cite its own supporting facts. Do not cite unrelated sections.
Use insufficient_evidence with null value and null SQL for an unavailable requested quantity. Conclusion verdicts mean supported, contradicted, or not_established. Only the requested proposition is scored. Do not add factual prose outside the structured fields. Reason codes are optional and are not scored.
Per-claim absolute numerical tolerances in requested units:
- march31_reserves_usd: usd - 0.5
- march31_circulation_usdc: usdc - 0.5
- march31_residual_usd: usd - 0.5
- coverage_change_bps: basis_points - 0.005
Use the public structure checker: python /workspace/check_answer.py /logs/artifacts/answer.json. It checks delivery only and contains no financial answers. No live source acquisition is needed.


For unit matching, the grader trims surrounding whitespace, ignores case, and treats runs of ordinary whitespace or underscores as a single underscore. It does not convert units or scales.
