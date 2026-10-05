# Results

**All scheduled attempts accounted for.**

Imported final records: **48/48**. Original verdicts available: **48**. Reviewed verdicts: **47**.
Unrecorded, queued and running slots are not zero-score model answers. Counts below retain the full planned denominator.
Original verdicts are immutable. Reviewed verdicts are separate scorer-versioned checks of the same retained bytes, not new model trials.

| Split | Arm | Original verified / planned | Original verdicts | Reviewed verified / planned | Reviewed verdicts |
|---|---|---:|---:|---:|---:|
| evaluation | A | 3 / 15 | 15 | 3 / 15 | 15 |
| evaluation | B | 1 / 15 | 15 | 1 / 15 | 15 |
| development | A | 4 / 9 | 9 | 4 / 9 | 9 |
| development | B | 3 / 9 | 9 | 3 / 9 | 8 |

## Numerical and independent checks

Passes / assessed checks are shown beside the planned counts above. Null checks are unassessed or inapplicable. Legacy conclusions cannot be split retrospectively without regrading.

| Scorer | Split | Arm | Numbers | Format | Evidence | Units/availability | SQL replay | Conclusion verdict | Conclusion reason | Conclusion evidence |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Original | evaluation | A | 13 / 13 | 13 / 15 | 7 / 15 | 13 / 15 | 7 / 13 | Unassessed | Unassessed | Unassessed |
| Original | evaluation | B | 12 / 13 | 13 / 15 | 7 / 15 | 13 / 15 | 10 / 13 | Unassessed | Unassessed | Unassessed |
| Original | development | A | 8 / 8 | 8 / 9 | 6 / 9 | 8 / 9 | 4 / 8 | Unassessed | Unassessed | Unassessed |
| Original | development | B | 8 / 8 | 8 / 9 | 8 / 9 | 8 / 9 | 4 / 8 | Unassessed | Unassessed | Unassessed |
| Corrected | evaluation | A | 13 / 13 | 13 / 15 | 7 / 13 | 13 / 13 | 7 / 13 | 11 / 11 | 8 / 11 | 8 / 11 |
| Corrected | evaluation | B | 13 / 14 | 13 / 15 | 7 / 13 | 13 / 13 | 10 / 13 | 10 / 10 | 6 / 10 | 6 / 10 |
| Corrected | development | A | 9 / 9 | 8 / 9 | 6 / 8 | 8 / 8 | 4 / 8 | 5 / 5 | 5 / 5 | 2 / 5 |
| Corrected | development | B | 8 / 8 | 8 / 8 | 8 / 8 | 8 / 8 | 4 / 8 | 5 / 5 | 5 / 5 | 4 / 5 |

## Diagnose the failure, not just the score

`None` means not assessed or not applicable, never a failed calculation. Evidence-ID requirements are distinct from semantic truth. Legacy conclusion checks combine verdict, reason and citations.

| Scorer | Split | Arm | Numbers correct, full task failed | Observed causes (nonexclusive) |
|---|---|---|---:|---|
| Original | evaluation | A | 10 | {'evidence_requirements': 6, 'conclusion_contract_unsplit': 5, 'replay': 6} |
| Original | evaluation | B | 11 | {'evidence_requirements': 6, 'conclusion_contract_unsplit': 7, 'replay': 2} |
| Original | development | A | 4 | {'evidence_requirements': 2, 'conclusion_contract_unsplit': 3, 'replay': 4} |
| Original | development | B | 5 | {'replay': 4, 'conclusion_contract_unsplit': 1} |
| Reviewed | evaluation | A | 10 | {'evidence_requirements': 6, 'conclusion_reason_or_evidence': 5, 'replay': 6} |
| Reviewed | evaluation | B | 12 | {'evidence_requirements': 6, 'conclusion_reason_or_evidence': 7, 'format': 1, 'replay': 2} |
| Reviewed | development | A | 5 | {'evidence_requirements': 2, 'conclusion_reason_or_evidence': 3, 'replay': 4, 'format': 1} |
| Reviewed | development | B | 5 | {'replay': 4, 'conclusion_reason_or_evidence': 1} |

## Every scheduled slot

| Slot | State | Original complete | Reviewed complete | Run | Original errors |
|---|---|---|---|---|---|
| final-wp01-A-1 | complete | True | True | 37280454673 |  |
| final-wp01-B-1 | complete | True | True | 37280454673 |  |
| final-wp01-B-2 | task_failed | False | False | 37280454673 | q1_rd:replay, sequential_change:replay |
| final-wp01-A-2 | complete | True | True | 37280454673 |  |
| final-wp01-A-3 | complete | True | True | 37280454673 |  |
| final-wp01-B-3 | complete | True | True | 37280454673 |  |
| final-wp02-B-1 | task_failed | False | False | 37280454673 | conclusion |
| final-wp02-A-1 | task_failed | False | False | 37280454673 | transfer_total:replay, transfer_total:evidence_context, conclusion |
| final-wp02-A-2 | task_failed | False | False | 37280454673 | format:ValueError |
| final-wp02-B-2 | task_failed | False | False | 37280454673 | transfer_total:replay |
| final-wp02-B-3 | complete | True | True | 37280454673 |  |
| final-wp02-A-3 | task_failed | False | False | 37280454673 | transfer_total:replay, conclusion |
| final-wp03-A-1 | task_failed | False | False | 37280454673 | p1_total:replay, p1_total:evidence_context, p2_total:replay, p2_total:evidence_context, as_of_growth:replay, as_of_growth:evidence_context, conclusion |
| final-wp03-B-1 | task_failed | False | False | 37280454673 | p1_total:evidence_context, p2_total:evidence_context, as_of_growth:evidence_context, conclusion |
| final-wp03-B-2 | task_failed | False | False | 37280454673 | p1_total:evidence_context, p2_total:evidence_context, as_of_growth:evidence_context, conclusion |
| final-wp03-A-2 | task_failed | False | False | 37280454673 | p1_total:replay, p1_total:evidence_context, p2_total:replay, p2_total:evidence_context, as_of_growth:replay, as_of_growth:evidence_context, conclusion |
| final-wp03-A-3 | task_failed | False | False | 37280454673 | p1_total:replay, p1_total:evidence_context, p2_total:replay, p2_total:evidence_context, as_of_growth:replay, as_of_growth:evidence_context |
| final-wp03-B-3 | task_failed | False | False | 37280454673 | p1_total:evidence_context, p2_total:evidence_context, as_of_growth:evidence_context, conclusion |
| final-wp04-B-1 | task_failed | False | False | 37280454673 | format:ValueError |
| final-wp04-A-1 | task_failed | False | False | 37280454673 | all_events:replay, max_per_tx:replay, difference:replay, conclusion |
| final-wp04-A-2 | task_failed | False | False | 37280454673 | conclusion |
| final-wp04-B-2 | task_failed | False | False | 37280454673 | all_events:evidence_context, max_per_tx:evidence_context, difference:evidence_context, conclusion |
| final-wp04-B-3 | task_failed | False | False | 37280454673 | conclusion |
| final-wp04-A-3 | task_failed | False | False | 37280454673 | format:ValueError |
| final-wp05-A-1 | task_failed | False | False | 37280454673 | naive_growth:replay, comparable_growth:replay, comparable_growth:evidence_context, conclusion |
| final-wp05-B-1 | task_failed | False | False | 37280454673 | naive_growth:replay, comparable_growth:replay |
| final-wp05-B-2 | task_failed | False | False | 37280454673 | naive_growth:replay, comparable_growth:replay |
| final-wp05-A-2 | task_failed | False | False | 37280454673 | naive_growth:replay, comparable_growth:replay |
| final-wp05-A-3 | complete | True | True | 37280454673 |  |
| final-wp05-B-3 | task_failed | False | Not assessed | 37280454673 | format:ValueError |
| final-wp06-B-1 | complete | True | True | 37280454673 |  |
| final-wp06-A-1 | task_failed | False | False | 37280454673 | reported_growth:evidence_context, matched_growth:evidence_context |
| final-wp06-A-2 | task_failed | False | False | 37280454673 | reported_growth:evidence_context, matched_growth:evidence_context |
| final-wp06-B-2 | task_failed | False | False | 37280454673 | reported_growth:evidence_context, matched_growth:evidence_context |
| final-wp06-B-3 | task_failed | False | False | 37280454673 | format:ValueError |
| final-wp06-A-3 | task_failed | False | False | 37280454673 | reported_growth:replay, reported_growth:evidence_context, matched_growth:replay, matched_growth:evidence_context |
| final-wp07-A-1 | task_failed | False | False | 37280454673 | q1_revenue:replay, q1_gross_profit:replay, q1_margin:replay, margin_change:replay |
| final-wp07-B-1 | task_failed | False | False | 37280454673 | q1_revenue:replay, q1_gross_profit:replay, q1_margin:replay, margin_change:replay |
| final-wp07-B-2 | task_failed | False | False | 37280454673 | q1_revenue:replay, q1_gross_profit:replay, q1_margin:replay, margin_change:replay |
| final-wp07-A-2 | complete | True | True | 37280454673 |  |
| final-wp07-A-3 | task_failed | False | False | 37280454673 | format:ValueError |
| final-wp07-B-3 | task_failed | False | False | 37280454673 | q1_margin:numerical, q1_margin:replay, margin_change:numerical, margin_change:replay |
| final-wp08-B-1 | task_failed | False | False | 37280454673 | transfer_total:evidence_context |
| final-wp08-A-1 | complete | True | True | 37280454673 |  |
| final-wp08-A-2 | complete | True | True | 37280454673 |  |
| final-wp08-B-2 | task_failed | False | False | 37280454673 | conclusion |
| final-wp08-B-3 | task_failed | False | False | 37280454673 | conclusion |
| final-wp08-A-3 | task_failed | False | False | 37280454673 | conclusion |

## Task outcomes and origins

| Task | Arm | Original complete / planned | Corrected complete / planned | Corrected coverage | Origin | Source group |
|---|---|---:|---:|---:|---|---|
| wp01 | A | 3 / 3 | 3 / 3 | 3 / 3 | primary_filing_facts | tesla-2024-q2 |
| wp01 | B | 2 / 3 | 2 / 3 | 3 / 3 | primary_filing_facts | tesla-2024-q2 |
| wp02 | A | 0 / 3 | 0 / 3 | 3 / 3 | synthetic | authored-event-ledger |
| wp02 | B | 1 / 3 | 1 / 3 | 3 / 3 | synthetic | authored-event-ledger |
| wp03 | A | 0 / 3 | 0 / 3 | 3 / 3 | synthetic | authored-dated-releases |
| wp03 | B | 0 / 3 | 0 / 3 | 3 / 3 | synthetic | authored-dated-releases |
| wp04 | A | 0 / 3 | 0 / 3 | 3 / 3 | synthetic_acquisition_downgrade | synthetic-usdc-window |
| wp04 | B | 0 / 3 | 0 / 3 | 3 / 3 | synthetic_acquisition_downgrade | synthetic-usdc-window |
| wp05 | A | 1 / 3 | 1 / 3 | 3 / 3 | synthetic | authored-migration |
| wp05 | B | 0 / 3 | 0 / 3 | 2 / 3 | synthetic | authored-migration |
| wp06 | A | 0 / 3 | 0 / 3 | 3 / 3 | synthetic | synthetic-coverage-expansion |
| wp06 | B | 1 / 3 | 1 / 3 | 3 / 3 | synthetic | synthetic-coverage-expansion |
| wp07 | A | 1 / 3 | 1 / 3 | 3 / 3 | primary_filing_facts | apple-2024-q2 |
| wp07 | B | 0 / 3 | 0 / 3 | 3 / 3 | primary_filing_facts | apple-2024-q2 |
| wp08 | A | 2 / 3 | 2 / 3 | 3 / 3 | synthetic_acquisition_downgrade | synthetic-usdc-window |
| wp08 | B | 0 / 3 | 0 / 3 | 3 / 3 | synthetic_acquisition_downgrade | synthetic-usdc-window |

## Score changes and retained input

Corrected scorer identity: `['1.2.0', 'a8072598d2ff7475ef6358236b1cbde45e290465dd0675939bb82e8a4c02e455']`. Full input hashes, original diagnostics and corrected diagnostics are in [scores.json](scores.json).

Strict completion changes among regraded slots: **0**.

Not regraded: final-wp05-B-3.
Historical normalized JSON is the input where original bytes are missing. It is never relabeled as original serialization. Missing answer bytes cannot yield a corrected verdict. Previous regrades remain under their content hashes.

## Cost and interpretation

Provider snapshot lifetime use: **0.769789131 USD**.
Snapshot time: 2026-10-05T11:15:27.710840+00:00. Original verified completions recorded by that snapshot: 14.
Lifetime includes exploration and failures. Snapshot reporting can lag. Slot deltas are not exact per-arm costs. Native zero token fields do not establish zero usage.

A and B use the same model. This is a small regression study, not a model leaderboard, significance test or production-reliability estimate.
The original matrix limited concurrency but did not enforce pair order. Actual start order and per-slot latency/cost/diagnostic fields are preserved in scores.json.
Five evaluation tasks are not five independent datasets. Two share the synthetic acquisition fallback. Development and evaluation remain separate.

| Split | Arm | Mean solve seconds | Recorded snapshot deltas USD | Unknown delta slots |
|---|---|---:|---:|---:|
| evaluation | A | 60.01 | 0.121025 | 0 |
| evaluation | B | 101.95 | 0.166759 | 0 |
| development | A | 55.23 | 0.043511 | 0 |
| development | B | 52.32 | 0.027177 | 0 |

Actual start order matches the preserved schedule: **True**. Recorded order: final-wp01-A-1, final-wp01-B-1, final-wp01-B-2, final-wp01-A-2, final-wp01-A-3, final-wp01-B-3, final-wp02-B-1, final-wp02-A-1, final-wp02-A-2, final-wp02-B-2, final-wp02-B-3, final-wp02-A-3, final-wp03-A-1, final-wp03-B-1, final-wp03-B-2, final-wp03-A-2, final-wp03-A-3, final-wp03-B-3, final-wp04-B-1, final-wp04-A-1, final-wp04-A-2, final-wp04-B-2, final-wp04-B-3, final-wp04-A-3, final-wp05-A-1, final-wp05-B-1, final-wp05-B-2, final-wp05-A-2, final-wp05-A-3, final-wp05-B-3, final-wp06-B-1, final-wp06-A-1, final-wp06-A-2, final-wp06-B-2, final-wp06-B-3, final-wp06-A-3, final-wp07-A-1, final-wp07-B-1, final-wp07-B-2, final-wp07-A-2, final-wp07-A-3, final-wp07-B-3, final-wp08-B-1, final-wp08-A-1, final-wp08-A-2, final-wp08-B-2, final-wp08-B-3, final-wp08-A-3.

Supplementary records: **12**. Their statuses, costs and original verdicts remain in scores.json. No additional inference was used for correction.
