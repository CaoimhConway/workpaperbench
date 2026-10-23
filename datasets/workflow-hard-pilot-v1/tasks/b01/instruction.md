# Microsoft cash capital outlay and nested PPE movements

Prepare Microsoft consolidated FY2025 capital-investment and asset-movement workpapers for the year ended June 30, 2025. Separate cash outlay from asset recognition and reconcile changes in total PPE and its finance-lease subset from June 30, 2024 to June 30, 2025. Use disclosed point values and retain signed residuals when the supplied disclosures do not completely explain movements. Do not assign those residuals to undocumented acquisitions, disposals or currency movements.

Read /workspace/sources.md and /workspace/evidence.json. Query /workspace/data.sqlite. The definitions, required columns, row keys, units, precision and assertions are in /workspace/output_contract.json. There is no starting SQL.

Deliver exactly /logs/artifacts/answer.json and the three SQL files named cash_investment.sql, ppe_bridge.sql, lease_movements.sql. Each JSON table entry names its SQL file and evidence IDs. Supply each requested table and claim exactly once, with no extra files. Use supported, contradicted or unresolved claim verdicts against the original dossier. The JSON schema is /workspace/schema.json. Optional notes are not semantically graded.

SQL must be read-only SELECT/CTE and recompute from the inputs. Controls change relevant observations or authored assumptions consistently, and may introduce explicitly independent reported-total discrepancies. Claim verdicts are graded on the original dossier only. Equivalent correct derivations and sufficient evidence paths are accepted. Row and column order are ignored. Each query returns at most 100 rows and 16 columns. No file access, writes, extensions or wall-clock dates. JSON is at most 65536 bytes, each SQL file at most 16384 UTF-8 bytes. Use safe lowercase SQL basenames.

Task ID: workflow-hard-pilot-v1-b01
