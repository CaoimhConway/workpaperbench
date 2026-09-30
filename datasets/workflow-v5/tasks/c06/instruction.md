# Financial workflow

Reconcile Alphabet Q2FY2025 year-over-year and sequential revenue growth. Preserve comparison-specific translation bases, separate currency from hedging, and attribute reported year-over-year growth across mutually exclusive revenue components. Assess the limit on a separate AI-product attribution.

Read the source headings, definitions and evidence locators in /workspace/sources.md and evidence.json. The input database is /workspace/data.sqlite. Its SQLite tables contain source-derived observations. The starting SQL is an authored research work product. Its defects are synthetic, not discovered issuer defects.

Deliver /logs/artifacts/answer.json and one read-only SELECT/CTE .sql file per requested named table, all in /logs/artifacts. In each JSON table entry, file is the SQL basename, for example reserve_bridge.sql, relative to answer.json. Absolute paths and directory prefixes are rejected. SQL basenames begin with a lowercase letter, followed by at most 40 lowercase letters, digits or underscores, then .sql. Create regular files without symlinks. Include each requested table and claim ID exactly once. The JSON schema is /workspace/schema.json and the public columns, units, keys and claim assertions are /workspace/output_contract.json. Use the literal claim IDs for the assertions stated there, with supported, contradicted or unresolved verdicts. A short optional note is not semantically graded. Cite sufficient facts and relevant period, unit, definition or scope context for each output. Additional unrelated sections fail evidence. Equivalent reviewed source paths are accepted, without a shortest-citation requirement.

Table column names are required, column order and row order are ignored. Keys are unique, duplicate output keys fail, and no row may be silently dropped. Ratios labeled percent must be multiplied by 100, and basis points by 10000. Monetary columns retain the specified units. Each query returns at most 100 rows and 16 columns, with no file access, DDL, writes, wall-clock dates or extensions. Answer JSON is at most 65536 bytes and each SQL file at most 16384 UTF-8 bytes. No additional artifact files.

Recompute from pristine inputs. Hidden synthetic controls exercise period filters, equivalent monetary scaling, component changes and unaffected outputs. Reported totals and components may disagree, and independently observed residuals must retain the discrepancy. Do not silently repair source observations. Conclusions refer to the original dossier only.

Task ID: workflow-v5-c06
