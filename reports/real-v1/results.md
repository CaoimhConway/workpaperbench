# Real-v1 results

Dataset `real-v1-76d0ba6152ff`, scorer 1.2.0, model `qwen/qwen3.6-35b-a3b`.

Historical results are a separate study. No scores carry over to changed tasks.

| Split | Arm | Strict / scheduled | Numbers / assessed | Conclusion verdict / assessed | Evidence / assessed | Replay / assessed | Verdict coverage | Retained / scheduled |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| evaluation | A | 4 / 15 | 15 / 15 | 10 / 11 | 8 / 14 | 10 / 14 | 15 / 15 | 15 / 15 |
| evaluation | B | 4 / 15 | 14 / 14 | 11 / 12 | 10 / 14 | 8 / 14 | 14 / 15 | 14 / 15 |
| development | A | 4 / 9 | 7 / 8 | 4 / 4 | 5 / 7 | 5 / 7 | 9 / 9 | 9 / 9 |
| development | B | 3 / 9 | 7 / 9 | 5 / 5 | 6 / 8 | 4 / 8 | 9 / 9 | 9 / 9 |

Strict completion requires all declared checks. A missing citation or reason does not establish an incorrect financial conclusion. Unassessed checks are pending, not zero accuracy.

The five evaluation tasks share some source bundles. Apple is a previously exposed regression task. This is not an independent-dataset or contamination-free study.

| Slot | Status | Strict | Numbers | Conclusion verdict | Errors |
|---|---|---|---|---|---|
| final-wp01-A-1 | complete | True | True | Pending |  |
| final-wp01-B-1 | complete | True | True | Pending |  |
| final-wp01-B-2 | complete | True | True | Pending |  |
| final-wp01-A-2 | complete | True | True | Pending |  |
| final-wp01-A-3 | complete | True | True | Pending |  |
| final-wp01-B-3 | complete | True | True | Pending |  |
| final-wp02-B-1 | task_failed | False | False | True | transfer_total:numerical, transfer_total:replay, conclusion |
| final-wp02-A-1 | task_failed | False | None | Pending | format:ValueError, transfer_total:not_assessed |
| final-wp02-A-2 | task_failed | False | True | Pending | format:ValueError |
| final-wp02-B-2 | task_failed | False | True | True | transfer_total:replay, transfer_total:evidence_context, conclusion |
| final-wp02-B-3 | task_failed | False | False | Pending | format:ValueError |
| final-wp02-A-3 | task_failed | False | False | True | transfer_total:numerical, transfer_total:replay, transfer_total:evidence_context |
| final-wp03-A-1 | task_failed | False | True | True | sample_fees:evidence_context, claimed_above_subsidy:evidence_context, conclusion |
| final-wp03-B-1 | complete | True | True | True |  |
| final-wp03-B-2 | task_failed | False | True | True | sample_fees:replay, claimed_above_subsidy:replay |
| final-wp03-A-2 | task_failed | False | True | True | sample_fees:evidence_context, claimed_above_subsidy:evidence_context, conclusion |
| final-wp03-A-3 | task_failed | False | True | True | conclusion |
| final-wp03-B-3 | task_failed | False | True | True | sample_fees:replay, claimed_above_subsidy:replay |
| final-wp04-B-1 | complete | True | True | True |  |
| final-wp04-A-1 | complete | True | True | True |  |
| final-wp04-A-2 | task_failed | False | True | Pending | format:ValueError |
| final-wp04-B-2 | task_failed | False | True | True | conclusion |
| final-wp04-B-3 | task_failed | False | True | True | circulating_growth:evidence_context |
| final-wp04-A-3 | task_failed | False | True | True | circulating_end:replay, circulating_growth:replay, reserve_headroom:replay |
| final-wp05-A-1 | complete | True | True | True |  |
| final-wp05-B-1 | task_failed | False | True | True | naive_growth:replay |
| final-wp05-B-2 | task_failed | False | True | True | naive_growth:replay, comparable_growth:replay |
| final-wp05-A-2 | task_failed | False | True | True | comparable_growth:evidence_context, conclusion |
| final-wp05-A-3 | task_failed | False | True | True | naive_growth:replay, comparable_growth:replay |
| final-wp05-B-3 | task_failed | False | True | True | comparable_growth:evidence_context, conclusion |
| final-wp06-B-1 | task_failed | False | True | True | sample_rate_change:replay, matched_rate_change:replay |
| final-wp06-A-1 | task_failed | False | True | True | sample_rate_change:replay, sample_rate_change:evidence_context, matched_rate_change:replay, matched_rate_change:evidence_context, conclusion |
| final-wp06-A-2 | task_failed | False | True | True | sample_rate_change:replay, matched_rate_change:replay |
| final-wp06-B-2 | task_failed | False | True | True | sample_rate_change:replay, matched_rate_change:replay |
| final-wp06-B-3 | task_failed | False | True | True | sample_rate_change:evidence_context, matched_rate_change:evidence_context, conclusion |
| final-wp06-A-3 | task_failed | False | True | True | sample_rate_change:evidence_context, matched_rate_change:evidence_context, conclusion |
| final-wp07-A-1 | complete | True | True | Pending |  |
| final-wp07-B-1 | infra_failed | Pending | Pending | Pending |  |
| final-wp07-B-2 | complete | True | True | Pending |  |
| final-wp07-A-2 | complete | True | True | Pending |  |
| final-wp07-A-3 | complete | True | True | Pending |  |
| final-wp07-B-3 | complete | True | True | Pending |  |
| final-wp08-B-1 | task_failed | False | True | False | conclusion |
| final-wp08-A-1 | task_failed | False | True | True | observed_outputs:replay, business_payments:availability_or_unit, unique_people:availability_or_unit, conclusion |
| final-wp08-A-2 | task_failed | False | True | False | observed_outputs:evidence_context, business_payments:evidence_context, business_payments:availability_or_unit, conclusion |
| final-wp08-B-2 | task_failed | False | True | True | observed_outputs:replay, business_payments:evidence_context, unique_people:evidence_context, conclusion |
| final-wp08-B-3 | task_failed | False | True | True | observed_outputs:replay, observed_outputs:evidence_context |
| final-wp08-A-3 | task_failed | False | True | True | observed_outputs:evidence_context, conclusion |

## Intervention interpretation

The new campaign has incomplete verdict coverage. Strict completion counts retain the scheduled denominator and cannot establish an intervention benefit.

A has full common instructions. B adds only the preserved contract-check skill. Three repeated attempts per task are not independent financial datasets. No significance or causal claim is made.

## Independent diagnostics

| Split | Arm | Conclusion reason / assessed | Conclusion evidence / assessed | Format / assessed |
|---|---|---:|---:|---:|
| evaluation | A | 8 / 11 | 5 / 11 | 14 / 15 |
| evaluation | B | 10 / 12 | 10 / 12 | 14 / 14 |
| development | A | 4 / 4 | 3 / 4 | 7 / 9 |
| development | B | 5 / 5 | 2 / 5 | 8 / 9 |

Actual order and original per-slot records are retained in [scores.json](scores.json). No official answer is repaired or retried for a better score.

Provider receipt as of 2026-10-06T13:13:14.000503+00:00: cumulative USD 1.508940909, including historical USD 0.769789131. New campaign increment USD 0.739151778. The unchanged dedicated lifetime cap is USD 20, below the USD 50 authorization.

Provider lifetime includes development and failed calls. Reporting can lag. Per-arm allocation and Actions invoice/storage charges are unknown.
