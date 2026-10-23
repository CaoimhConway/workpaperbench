# Customer collections through a receivables-financing transition

Assess whether Constellation Energy Corporation consolidated cash generation improved in the nine months ended September 30, 2025 relative to the same 2024 period. Present both periods on a consistent NER-facility basis with customer collections in operating activities and purchaser principal cash in financing activities. Reconstruct the operating, investing and financing totals, quantify the change with and without collateral cash, and reconcile the 2024 retained-interest movement from its disclosures. Keep separate tariff receivables sales within their reported treatment.

Read /workspace/sources.md and /workspace/evidence.json. Query /workspace/data.sqlite. The definitions, required columns, row keys, units, precision and assertions are in /workspace/output_contract.json. There is no starting SQL.

Deliver exactly /logs/artifacts/answer.json and the three SQL files named cashflow_recast.sql, cash_generation_change.sql, retained_interest_bridge.sql. Each JSON table entry names its SQL file and evidence IDs. Supply each requested table and claim exactly once, with no extra files. Use supported, contradicted or unresolved claim verdicts against the original dossier. The JSON schema is /workspace/schema.json. Optional notes are not semantically graded.

SQL must be read-only SELECT/CTE and recompute from the inputs. Controls change relevant observations or authored assumptions consistently, without redefining the financial rules. Claim verdicts are graded on the original dossier only. Equivalent correct derivations and sufficient evidence paths are accepted. Row and column order are ignored. Each query returns at most 100 rows and 16 columns. No file access, writes, extensions or wall-clock dates. JSON is at most 65536 bytes, each SQL file at most 16384 UTF-8 bytes. Use safe lowercase SQL basenames.

Task ID: workflow-hard-eval-v1-c01
