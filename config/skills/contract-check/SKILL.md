---
name: contract-check
description: Review the requested workpaper contract before publishing.
---

Before calculating, make a short internal checklist from the supplied request. Identify the task identifier, the exact requested claim identifiers, the canonical units, the proposition if present, and the output location. Treat supporting calculations as working notes unless they are requested output claims.

Read the supplied records and definitions before selecting a population or comparing periods. Keep publication eligibility, metric definitions, coverage, event identity, and units attached to the operands. Distinguish an unavailable input from an observed zero. Scope any conclusion to the precise proposition and the evidence actually supplied.

For each answer, use the exact supporting record identifiers from the evidence catalog. Include the operands and the definitions needed for that claim. Do not substitute descriptive prose for identifiers or cite every record without checking its relevance.

Check each calculation as a read-only SQL statement over the supplied tables. Confirm that it returns one row and one numeric column named value. Make the query recompute from the data rather than return a remembered number. Keep the original numerical precision until the final output.

Before publishing, compare the output with the checklist. Remove extra claims, confirm required fields and nulls, and verify units, identifiers, evidence, and conclusion scope. Run the supplied structural checker when available. Remember that structural validity alone does not establish the calculation, evidence support, or replay behavior.
