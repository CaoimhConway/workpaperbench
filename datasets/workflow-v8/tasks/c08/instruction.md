# Financial workflow

Reconcile Broadcom FY2025, both supplied Q4 periods and Q3FY2025. Calculate signed adjusted net income, match diluted share bases and quantify the effect of using an incorrect GAAP denominator. Attribute annual and Q4 revenue growth by segment while separating tax, discontinued-operation and price-attribution scope.

Read the source headings, definitions and evidence locators in /workspace/sources.md and evidence.json. The input database is /workspace/data.sqlite. Its SQLite tables contain source-derived observations. Construct all requested SQL from these observations. This construction track supplies no starting SQL.

Deliver /logs/artifacts/answer.json and one read-only SELECT/CTE .sql file per requested named table, all in /logs/artifacts. In each JSON table entry, file is the SQL basename, for example reserve_bridge.sql, relative to answer.json. Absolute paths and directory prefixes are rejected. SQL basenames begin with a lowercase letter, followed by at most 40 lowercase letters, digits or underscores, then .sql. Create regular files without symlinks. Include each requested table and claim ID exactly once. The JSON schema is /workspace/schema.json and the public columns, units, keys and claim assertions are /workspace/output_contract.json. Use the literal claim IDs for the assertions stated there, with supported, contradicted or unresolved verdicts. A short optional note is not semantically graded. Cite sufficient supporting source IDs for each output. IDs may appear alone or inside explanations, with multiple IDs in one entry. Explanation-only entries do not supply evidence. Every cited ID must be relevant and known. Additional unrelated sections fail. Prose is not an entailment check and cannot repair incorrect numbers.

Supported means the supplied evidence entails the assertion. Contradicted means it entails the negation. Unresolved means neither follows. A claim that the supplied dossier explicitly reports a quantity is contradicted when the supplied scope explicitly omits it. A claim about the unknown economic quantity itself remains unresolved. Do not infer zero from missing information. No label count or order is promised.

Text columns declare canonical values and accepted source-label aliases. Aliases refer to the same economic category, never a different period, unit or measure. Duplicate keys after normalization fail. Different SQL, row order and column order are accepted. Numeric tolerances are unchanged.

Table column names are required, column order and row order are ignored. Keys are unique, duplicate output keys fail, and no row may be silently dropped. Ratios labeled percent must be multiplied by 100, and basis points by 10000. Monetary columns retain the specified units. Each query returns at most 100 rows and 16 columns, with no file access, DDL, writes, wall-clock dates or extensions. Answer JSON is at most 65536 bytes and each SQL file at most 16384 UTF-8 bytes. No additional artifact files.

Recompute from pristine inputs. Hidden synthetic controls exercise period filters, equivalent monetary scaling, component changes and unaffected outputs. Reported totals and components may disagree, and independently observed residuals must retain the discrepancy. Do not silently repair source observations. Conclusions refer to the original dossier only.

Task ID: workflow-v8-c08
