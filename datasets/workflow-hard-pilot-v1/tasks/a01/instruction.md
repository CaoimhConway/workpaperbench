# Ahold Delhaize comparable sales across merger scope and calendars

Prepare a 2016-versus-2015 sales workpaper for Ahold Delhaize. Use the disclosed pro forma business perimeter at reported exchange rates. Match durations between years within each former business by excluding the additional former-Ahold week in 2015. Retain the different former-Ahold and former-Delhaize reporting calendars. Reconstruct Q4 2016 from the IFRS and adjustment disclosures, report segment comparisons for FY, Q4 and the pre-Q4 reporting period, and explain the group annual sales-change difference from statutory reporting numerically. This is not an organic, same-store or constant-currency estimate.

Read /workspace/sources.md and /workspace/evidence.json. Query /workspace/data.sqlite. The definitions, required columns, row keys, units, precision and assertions are in /workspace/output_contract.json. There is no starting SQL.

Deliver exactly /logs/artifacts/answer.json and the three SQL files named quarter_scope.sql, comparable_periods.sql, annual_change_bridge.sql. Each JSON table entry names its SQL file and evidence IDs. Supply each requested table and claim exactly once, with no extra files. Use supported, contradicted or unresolved claim verdicts against the original dossier. The JSON schema is /workspace/schema.json. Optional notes are not semantically graded.

SQL must be read-only SELECT/CTE and recompute from the inputs. Controls change relevant observations or authored assumptions consistently, and may introduce explicitly independent reported-total discrepancies. Claim verdicts are graded on the original dossier only. Equivalent correct derivations and sufficient evidence paths are accepted. Row and column order are ignored. Each query returns at most 100 rows and 16 columns. No file access, writes, extensions or wall-clock dates. JSON is at most 65536 bytes, each SQL file at most 16384 UTF-8 bytes. Use safe lowercase SQL basenames.

Task ID: workflow-hard-pilot-v1-a01
