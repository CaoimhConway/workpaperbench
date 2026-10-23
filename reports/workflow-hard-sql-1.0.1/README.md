# Experimental SQL compatibility correction

Worker `workflow-hard-sql-1.0.1` keeps SQLite temporary sorting and grouping
data in memory. The memory, CPU, time, output and filesystem limits are unchanged.
It differs from worker 1.0.0 by one `PRAGMA temp_store=MEMORY` statement.
Baseline and development dataset workers remain unchanged.

A retained authored alternative enumerates conversion choices and groups their
allocations. Under SQLite 3.40.1, worker 1.0.0 attempts a temporary disk write
and fails with `SQLITE_IOERR_WRITE` on the original and all nine controls.
Worker 1.0.1 returns the correct 88 rows on all ten databases in under 0.04
seconds per query, with maximum observed resident memory of 22,004 KiB.
The database hashes are unchanged. The [regression record](grouped-query-regression.json)
preserves the observations and binds the retained original receipt separately.
The [exact SQL fixture](../../tests/fixtures/workflow_hard_grouped_sale_allocations.sql)
is included for reproduction.

The revised packages use manifest `workflow-hard-eval-v1-canonical-f683af9b3079`.
All 63 focused tests pass, including 47 SQL boundary probes, ten grouped-query
comparisons, an immutability guard and five package tests. All 20 legitimate
workpaper variants pass and all 49 targeted incorrect variants fail.
[Verification](verification.json) and [package comparison](package-comparison.json)
record these checks. Candidate-visible files, financial answers, controls,
evidence paths and worked references are byte-identical to the executed freeze.

The correction and its [uniform reassessment protocol](../../config/hard-evaluation-20261023-r2/sql-reassessment.json)
were fixed from authored evidence before any final-evaluation submission or
score was inspected. The original campaign continues under worker 1.0.0.
Its original outcomes remain separate. Reassessment applies worker 1.0.1 to
every scheduled submission without edits or new inference, including missing
or delivery-failed submissions. It is not a campaign executed entirely under
the revised worker.
