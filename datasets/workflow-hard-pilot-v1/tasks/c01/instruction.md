# Apple joint revenue exposure and sharp stress-loss bounds

Assess Apple FY2024 revenue exposure to the authored regional demand stress in stress_rates. The source discloses worldwide Products and Services sales and costs, and country sales totals, but no joint sales table. Calculate exact worldwide gross profit and margins, feasible bounds on Products sales in each geography, and the tightest possible loss intervals for total revenue and gross profit under the stated scenario. Do not substitute proportional allocation for the missing joint sales disclosure.

Read /workspace/sources.md and /workspace/evidence.json. Query /workspace/data.sqlite. The definitions, required columns, row keys, units, precision and assertions are in /workspace/output_contract.json. There is no starting SQL.

Deliver exactly /logs/artifacts/answer.json and the three SQL files named worldwide_mix.sql, regional_product_bounds.sql, stress_bounds.sql. Each JSON table entry names its SQL file and evidence IDs. Supply each requested table and claim exactly once, with no extra files. Use supported, contradicted or unresolved claim verdicts against the original dossier. The JSON schema is /workspace/schema.json. Optional notes are not semantically graded.

SQL must be read-only SELECT/CTE and recompute from the inputs. Controls change relevant observations or authored assumptions consistently, and may introduce explicitly independent reported-total discrepancies. Claim verdicts are graded on the original dossier only. Equivalent correct derivations and sufficient evidence paths are accepted. Row and column order are ignored. Each query returns at most 100 rows and 16 columns. No file access, writes, extensions or wall-clock dates. JSON is at most 65536 bytes, each SQL file at most 16384 UTF-8 bytes. Use safe lowercase SQL basenames.

Task ID: workflow-hard-pilot-v1-c01
