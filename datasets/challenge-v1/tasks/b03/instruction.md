Using the June 30, 2025 detailed Financial Figures and Reserves Report and the issuer release, independently reconstruct `reserve_assets_usd` (USD) from the reserve asset line items. Derive `net_token_liability_usd` (USD) from the report-defined token liability inputs. Report `company_asset_excess_usd` (USD) as reconstructed reserve assets less detailed report company liabilities and `release_liability_delta_usd` (USD), oriented as release amount minus detailed report amount. Assess whether the two publications report the same exact June 30 company total liabilities.

Task identifier: challenge-v1-b03.
Inputs are in /workspace: data.sqlite, evidence.json, sources.md, schema.json and check_answer.py.
Write one workpaper to /logs/artifacts/answer.json, following schema.json. Use exactly the requested claim IDs and units.
For each answered claim, supply a finite number and deterministic read-only SQLite returning one row and one numeric column. Any column alias is accepted.
Calculations must recompute on pristine original inputs and synthetic schema-compatible controls. Controls can change observations, reorder rows and change irrelevant periods. No hidden control values are supplied. Conclusions are scored on the original dossier only.
Cite the stable section IDs supporting each claim, including required definitions and period or population context. Equivalent source paths are accepted. Shared context_evidence may hold common definitions, while each claim must cite its own supporting facts. Do not cite unrelated sections.
Use insufficient_evidence with null value and null SQL for an unavailable requested quantity. Conclusion verdicts mean supported, contradicted, or not_established. Only the requested proposition is scored. Do not add factual prose outside the structured fields. Reason codes are optional and are not scored.
Per-claim absolute numerical tolerances in requested units:
- reserve_assets_usd: usd - 0.5
- net_token_liability_usd: usd - 0.5
- company_asset_excess_usd: usd - 0.5
- release_liability_delta_usd: usd - 0.5
Use the public structure checker: python /workspace/check_answer.py /logs/artifacts/answer.json. It checks delivery only and contains no financial answers. No live source acquisition is needed.


For unit matching, the grader trims surrounding whitespace, ignores case, and treats runs of ordinary whitespace or underscores as a single underscore. It does not convert units or scales.
