# Ashtead distributions under a springing fixed-charge covenant

Assess three explicitly hypothetical twelve-month funding cases using the Ashtead Group ABL terms and facility observations at April 30, 2025. Test the proposed special dividends without new equity, find the sharp upper limit on special dividends, and find the sharp lower limit on cash equity needed for each target distribution. Apply the disclosed covenant only when it is applicable. Report whether each limit is actually attainable. This is a conditional funding analysis, not a company forecast or legal authorization to pay dividends.

Read /workspace/sources.md and /workspace/evidence.json. Query /workspace/data.sqlite. The definitions, required columns, row keys, units, precision and assertions are in /workspace/output_contract.json. There is no starting SQL.

Deliver exactly /logs/artifacts/answer.json and the three SQL files named proposal_tests.sql, distribution_frontier.sql, equity_support.sql. Each JSON table entry names its SQL file and evidence IDs. Supply each requested table and claim exactly once, with no extra files. Use supported, contradicted or unresolved claim verdicts against the original dossier. The JSON schema is /workspace/schema.json. Optional notes are not semantically graded.

SQL must be read-only SELECT/CTE and recompute from the inputs. Controls change relevant observations or authored assumptions consistently, without redefining the financial rules. Claim verdicts are graded on the original dossier only. Equivalent correct derivations and sufficient evidence paths are accepted. Row and column order are ignored. Each query returns at most 100 rows and 16 columns. No file access, writes, extensions or wall-clock dates. JSON is at most 65536 bytes, each SQL file at most 16384 UTF-8 bytes. Use safe lowercase SQL basenames.

Task ID: workflow-hard-pilot-v2-a01
