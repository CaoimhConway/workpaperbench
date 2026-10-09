# Financial workflow

Reconcile Adobe FY2025 GAAP and adjusted operating performance before using next-year ARR guidance. Preserve each disclosed quarterly comparison, quantify the annual change in the adjustment gap by component, and show why growth rates differ. Build an ARR basis bridge from observed FY2025 exit to revalued FY2026 opening and the mechanically implied target on the disclosed growth basis. Keep forecasts and ARR stock measures distinct from recognized revenue.

Read the source headings, definitions and evidence locators in /workspace/sources.md and evidence.json. The input database is /workspace/data.sqlite. Its SQLite tables contain source-derived observations. The starting SQL is an authored research work product. Its defects are synthetic, not discovered issuer defects.

Deliver /logs/artifacts/answer.json and one read-only SELECT/CTE .sql file per requested named table, all in /logs/artifacts. In each JSON table entry, file is the SQL basename, for example reserve_bridge.sql, relative to answer.json. Absolute paths and directory prefixes are rejected. SQL basenames begin with a lowercase letter, followed by at most 40 lowercase letters, digits or underscores, then .sql. Create regular files without symlinks. Include each requested table and claim ID exactly once. The JSON schema is /workspace/schema.json and the public columns, units, keys and claim assertions are /workspace/output_contract.json. Use the literal claim IDs for the assertions stated there, with supported, contradicted or unresolved verdicts. A short optional note is not semantically graded. Cite each output's supporting evidence IDs.

Table column names are required, column order and row order are ignored. Keys are unique, duplicate output keys fail, and no row may be silently dropped. Ratios labeled percent must be multiplied by 100, and basis points by 10000. Monetary columns retain the specified units. Each query returns at most 100 rows and 16 columns, with no file access, DDL, writes, wall-clock dates or extensions. Answer JSON is at most 65536 bytes and each SQL file at most 16384 UTF-8 bytes. No additional artifact files.

Recompute from pristine inputs. Reviewed synthetic controls exercise equivalent scaling, component changes and behavior preservation. Later disclosures outside the requested periods do not change the requested outputs.

Task ID: workflow-v4-c02
