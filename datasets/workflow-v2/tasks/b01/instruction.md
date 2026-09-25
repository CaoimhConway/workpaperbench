# Financial workflow

Audit the supplied SBC research SQL against the two reserve reports. Diagnose which starting calculations need repair and which are valid. Deliver coverage and residuals by economic observation date, preserve the valid signature-lag calculation, and bridge the cash, government-debt, reserve and circulation changes from May to June. Treat repeated identical exports as one report, while preserving different economic dates even when their amounts are equal. Determine whether these snapshots identify payments volume.

Read the source headings, definitions and evidence locators in /workspace/sources.md and evidence.json. The SQLite tables contain source-derived observations. The starting SQL is an authored research work product. Its defects are synthetic, not discovered issuer defects.

Deliver /logs/artifacts/answer.json and one read-only SELECT/CTE .sql file per requested named table. The JSON schema is /workspace/schema.json and the public columns, units, keys and claim assertions are /workspace/output_contract.json. Use the literal claim IDs for the assertions stated there, with supported, contradicted or unresolved verdicts. A short optional note is not semantically graded. Cite each output's supporting evidence IDs.

Table column names are required, column order and row order are ignored. Keys are unique, duplicate output keys fail, and no row may be silently dropped. Ratios labeled percent must be multiplied by 100, and basis points by 10000. Monetary columns retain the specified units. Each query returns at most 100 rows and 16 columns, with no file access, DDL, writes, wall-clock dates or extensions. Answer JSON is at most 65536 bytes and each SQL file at most 16384 UTF-8 bytes. No additional artifact files.

Recompute from pristine inputs. Hidden synthetic controls exercise the declared period filters, equivalent monetary scaling, meaningful component changes and unaffected outputs. SBC also tests duplicate exports and distinct economic dates with equal amounts. Required categories for Block are transaction, subscription, hardware, bitcoin and acquired_technology_amortization in the profit bridge. FY2024 and FY2025 each have fiscal quarters 1 and 2 in the Microsoft model.

Task ID: workflow-v2-b01
