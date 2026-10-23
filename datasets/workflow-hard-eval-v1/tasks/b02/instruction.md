# Reddit liquidation proceeds and conversion-dependent ownership

Assess hypothetical all-cash liquidation offers using Reddit's December 31, 2023 issued capital and the supplied pre-IPO rights. Calculate proceeds received by each original security cohort for every offer. Find the total proceeds and common-share payout at each nonmandatory series' voluntary conversion indifference point. Find the infimum of total proceeds that meets each owner cash target, and determine whether that infimum itself meets the target. These are counterfactual liquidation sensitivities, not the actual IPO or a GAAP EPS calculation.

Read /workspace/sources.md and /workspace/evidence.json. Query /workspace/data.sqlite. The definitions, required columns, row keys, units, precision and assertions are in /workspace/output_contract.json. There is no starting SQL.

Deliver exactly /logs/artifacts/answer.json and the three SQL files named sale_allocations.sql, conversion_frontiers.sql, owner_funding.sql. Each JSON table entry names its SQL file and evidence IDs. Supply each requested table and claim exactly once, with no extra files. Use supported, contradicted or unresolved claim verdicts against the original dossier. The JSON schema is /workspace/schema.json. Optional notes are not semantically graded.

SQL must be read-only SELECT/CTE and recompute from the inputs. Controls change relevant observations or authored assumptions consistently, without redefining the financial rules. Claim verdicts are graded on the original dossier only. Equivalent correct derivations and sufficient evidence paths are accepted. Row and column order are ignored. Each query returns at most 100 rows and 16 columns. No file access, writes, extensions or wall-clock dates. JSON is at most 65536 bytes, each SQL file at most 16384 UTF-8 bytes. Use safe lowercase SQL basenames.

Task ID: workflow-hard-eval-v1-b02
