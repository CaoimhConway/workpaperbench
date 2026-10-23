# Albertsons collateral availability and inventory purchase funding

For the hypothetical eligible-collateral cases, apply the August 27, 2025 Albertsons ABL terms to prepare borrowing-base certificates for ordinary and seasonal advance rates. Test each stated inventory purchase and calculate the largest purchase that the facility can fund under each case. Use the prescribed purchase mix and post-purchase collateral values. These are conditional credit-capacity calculations, not observed issuer availability or legal transaction approvals.

Read /workspace/sources.md and /workspace/evidence.json. Query /workspace/data.sqlite. The definitions, required columns, row keys, units, precision and assertions are in /workspace/output_contract.json. There is no starting SQL.

Deliver exactly /logs/artifacts/answer.json and the three SQL files named certificates.sql, purchase_plans.sql, funding_limits.sql. Each JSON table entry names its SQL file and evidence IDs. Supply each requested table and claim exactly once, with no extra files. Use supported, contradicted or unresolved claim verdicts against the original dossier. The JSON schema is /workspace/schema.json. Optional notes are not semantically graded.

SQL must be read-only SELECT/CTE and recompute from the inputs. Controls change relevant observations or authored assumptions consistently, without redefining the financial rules. Claim verdicts are graded on the original dossier only. Equivalent correct derivations and sufficient evidence paths are accepted. Row and column order are ignored. Each query returns at most 100 rows and 16 columns. No file access, writes, extensions or wall-clock dates. JSON is at most 65536 bytes, each SQL file at most 16384 UTF-8 bytes. Use safe lowercase SQL basenames.

Task ID: workflow-hard-eval-v1-a01
