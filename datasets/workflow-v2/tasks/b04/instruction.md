# Financial workflow

Audit the Robinhood FY2025 research project without assuming a repair is required. Retain valid SQL and document any identifiable defects. Reconcile adjusted expenses, including negative prior settlement amounts and both the reported and a consistently credit-excluded expense basis. Attribute annual revenue growth across transaction, interest and other revenue. Separate app and Bitstamp crypto volume in Q4 and preliminary January, normalizing duration only as a monthly arithmetic average. Resolve the scope of any organic asset-growth inference.

Read the source headings, definitions and evidence locators in /workspace/sources.md and evidence.json. The SQLite tables contain source-derived observations. The starting SQL is an authored research work product. Its defects are synthetic, not discovered issuer defects.

Deliver /logs/artifacts/answer.json and one read-only SELECT/CTE .sql file per requested named table. The JSON schema is /workspace/schema.json and the public columns, units, keys and claim assertions are /workspace/output_contract.json. Use the literal claim IDs for the assertions stated there, with supported, contradicted or unresolved verdicts. A short optional note is not semantically graded. Cite each output's supporting evidence IDs.

Table column names are required, column order and row order are ignored. Keys are unique, duplicate output keys fail, and no row may be silently dropped. Ratios labeled percent must be multiplied by 100, and basis points by 10000. Monetary columns retain the specified units. Each query returns at most 100 rows and 16 columns, with no file access, DDL, writes, wall-clock dates or extensions. Answer JSON is at most 65536 bytes and each SQL file at most 16384 UTF-8 bytes. No additional artifact files.

Recompute from pristine inputs. Reviewed synthetic controls exercise equivalent scaling, component changes and behavior preservation. Later disclosures outside the requested periods do not change the requested outputs.

Task ID: workflow-v2-b04
