# BMS acquisition costs, cash funding and performance bases

Assess the Celgene/Otezla and MyoKardia transactions using BMS consolidated FY2020 disclosures. Reconstruct accounting acquisition bases and disclosed transaction cash, reconcile their cash-payment components with the company cash-flow statements for 2019 and 2020, and evaluate the specified revenue and pretax-earnings views. All amounts are USD million except percentages. Use the finalized Celgene allocation in this filing.

Read /workspace/sources.md and /workspace/evidence.json. Query /workspace/data.sqlite. The definitions, required columns, row keys, units, precision and assertions are in /workspace/output_contract.json. There is no starting SQL.

Deliver exactly /logs/artifacts/answer.json and the three SQL files named acquisition_bases.sql, cash_coverage.sql, performance_views.sql. Each JSON table entry names its SQL file and evidence IDs. Supply each requested table and claim exactly once, with no extra files. Use supported, contradicted or unresolved claim verdicts against the original dossier. The JSON schema is /workspace/schema.json. Optional notes are not semantically graded.

SQL must be read-only SELECT/CTE and recompute from the inputs. Controls change relevant observations or authored assumptions consistently, without redefining the financial rules. Claim verdicts are graded on the original dossier only. Equivalent correct derivations and sufficient evidence paths are accepted. Row and column order are ignored. Each query returns at most 100 rows and 16 columns. No file access, writes, extensions or wall-clock dates. JSON is at most 65536 bytes, each SQL file at most 16384 UTF-8 bytes. Use safe lowercase SQL basenames.

Task ID: workflow-hard-eval-v1-b01
