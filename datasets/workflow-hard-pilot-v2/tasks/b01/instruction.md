# Veeco conversion funding and earnings-dependent dilution

Assess Veeco consolidated convertible-note exposure using the December 31, 2024 capital structure. Calculate gross note settlement funding and share issuance across the authored maturity-price scenarios. Separately calculate basic and diluted EPS across the hypothetical price and earnings scenarios. Find the share price that reaches the specified gross-issuance target and the net-income neutrality boundary for each note with optional principal settlement at the threshold-case price. These are sensitivities of frozen inputs, not forecasts or a reconstruction of actual FY2024 EPS.

Read /workspace/sources.md and /workspace/evidence.json. Query /workspace/data.sqlite. The definitions, required columns, row keys, units, precision and assertions are in /workspace/output_contract.json. There is no starting SQL.

Deliver exactly /logs/artifacts/answer.json and the three SQL files named settlement_scenarios.sql, diluted_eps.sql, thresholds.sql. Each JSON table entry names its SQL file and evidence IDs. Supply each requested table and claim exactly once, with no extra files. Use supported, contradicted or unresolved claim verdicts against the original dossier. The JSON schema is /workspace/schema.json. Optional notes are not semantically graded.

SQL must be read-only SELECT/CTE and recompute from the inputs. Controls change relevant observations or authored assumptions consistently, without redefining the financial rules. Claim verdicts are graded on the original dossier only. Equivalent correct derivations and sufficient evidence paths are accepted. Row and column order are ignored. Each query returns at most 100 rows and 16 columns. No file access, writes, extensions or wall-clock dates. JSON is at most 65536 bytes, each SQL file at most 16384 UTF-8 bytes. Use safe lowercase SQL basenames.

Task ID: workflow-hard-pilot-v2-b01
