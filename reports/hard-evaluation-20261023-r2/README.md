# Financial reasoning supplement calibration

Twelve scheduled attempts compare three model-and-agent configurations on four
source-grounded financial tasks. Each configuration received one fresh attempt
per task. The financial definitions, observations and controls were frozen before
candidate inference. All twelve slots are retained, without replacement attempts
or final-outcome task selection.

Results are descriptive. One task moves a four-task score by 25 percentage
points. Missing workpapers, citation failures and runtime limits are distinguished
from numerical mistakes. These data do not establish a stable model ranking or
comparability with other benchmarks.

## Results

| Task | GLM-5.3 | DeepSeek v4.1 Flash 1017 | GPT-6.1 Sol |
| --- | --- | --- | --- |
| a01, borrowing capacity | Incomplete delivery | Pass | Pass |
| b01, acquisitions | Pass | Numerically correct, missing evidence | Pass |
| b02, liquidation rights | Incomplete delivery | Incomplete delivery | Pass |
| c01, receivables financing | Pass after evidence correction | Timeout, no delivery | Numerical error |
| **Corrected complete workpapers** | **2/4** | **1/4** | **3/4** |

Original scores were 1/4, 1/4 and 3/4 respectively. The worker-only correction
changes no verdict. The evidence correction accepts GLM c01 and repairs one
DeepSeek b01 table's evidence diagnostic without changing that task's overall
failure. The [summary](summary.json) preserves all three assessment identities.
These are all-scheduled-slot completion counts, not financial-error counts.

## Conditions and execution

The [frozen matrix](../../config/hard-evaluation-20261023-r2/manifest.json) binds
source commit `3fbc022233bf2b6f3c621228fcd8659d37795552`, configuration commit
`61b969f054846a33310000a8da80ff64f50d11b7` and executed manifest
`workflow-hard-eval-v1-canonical-a13e5bdb16c3`. The source archive and all four
task packages were checked against those identities. All sixty native runtime
materialization proofs match. The separate verifier has no inference credential,
network or privileged socket. Candidate-visible materials exclude references,
controls, grading assets and repository history.

GLM-5.3 used OpenRouter's `wafer/us` route with FP4. DeepSeek used
`deepseek/deepseek-v4.1-flash-1017` on the official `deepseek` route, with
quantization unreported. Both used native Terminus-2, high reasoning, 24 turns,
3,600 seconds, a 16,384 output-token cap and the previously qualified settings.
Native output-length recovery remains enabled. GPT-6.1 Sol used high reasoning
through native Codex 0.162.0-alpha.17.2 and subscription authentication, with the
same wall time. Its native client has no equivalent turn or output-token cap.
These are configuration comparisons, with different tools, context management
and provider routes. Model metadata is not independent backend attestation.
Installed agents can read their inference credentials through terminal tools.

A controller interruption delayed collection of the last DeepSeek attempt and
launch of the four then-unstarted Sol attempts. The native DeepSeek result had
already finished and was collected without relaunching. The four Sol slots then
ran with the original frozen configuration. No scores or candidate workpapers
were inspected until all twelve attempts finished. The interrupted controller's
exit status and elapsed time are unknown. Native timestamps and the recovery
record remain in [verification.json](verification.json).

DeepSeek c01 reached the 3,600-second native timeout during an API request.
Its trace records repeated output-length recovery, 48 requests, 47 retained
responses and 29 length-limited responses. It delivered no workpaper. This is a
runtime/output-budget failure, not evidence of an incorrect financial answer.
The native timeout is recorded separately from the controller interruption.

## Costs and retained evidence

The settled OpenRouter charge for this matrix was **$1.393635383**. Retained
responses and their provider generation records account for $1.383924533.
The remaining $0.009710850 appeared during the final timed-out DeepSeek slot,
whose last request has no retained response. No generation ID or token count
is invented for that residual. Token totals for that slot cover retained
responses only. GLM accounts for $0.693013589, and DeepSeek's observed key
usage for its four slots totals $0.700621794. The measured subscription charge
for Sol is unknown.

Including the preceding two-task development calibration, this run used
$2.005901718 of OpenRouter credit. The final observed balance was $5.152327731.
No funding limit or reset setting changed. The earlier three-task pilot has its
own report and is excluded from these campaign totals.

[Receipts](receipts), [saved workpapers](workpapers), [all-slot ledger](ledger.json),
[original results](results.json) and [failure inventory](failure-inventory.json)
retain exact submission hashes, scores, configuration checks, termination and
usage observations. Raw traces remain local. Credential-pattern checks found no
authentication secrets in the exported records or the 441 retained archive
members inspected. Optional explanatory prose has no semantic score.

## Grading corrections

The original worker-only reassessment uses
`workflow-hard-eval-v1-canonical-f683af9b3079`. It applies worker 1.0.1 to the
unchanged workpapers. The correction was verified using authored SQL before
any final output was inspected. See the [SQL compatibility record](../workflow-hard-sql-1.0.1/README.md)
and the [worker-only reassessment](reassessment.json).

Output review identified two overly restrictive evidence paths. BMS performance
can be supported by s05+s06+s08: the earnings disclosure supplies all three
acquisition-date expense components and the contingent-consideration effect,
the pro forma disclosure supplies the comparator, and s08 defines the diagnostic.
Constellation's retained-interest bridge can be supported by s02+s05: the
transfer/collection facts and beginning/ending funding and DPP balances suffice.
Its s07 cash-flow presentation definition is unnecessary for this stock bridge.

The corrected package identity is
`workflow-hard-eval-v1-canonical-372b3270ea4b`. It adds only those sufficient
paths. Candidate-visible files, numerical answers, controls, claim verdicts,
worker, source facts and references are unchanged. This correction follows
outcome review and is explicitly separate from the executed condition. See the
[protocol](../../config/hard-evaluation-20261023-r2/evidence-reassessment.json),
[correction verification](../workflow-hard-evidence-v1/README.md) and
[evidence-corrected reassessment](evidence-reassessment.json).

Both reassessments include every scheduled slot. Each delivery-valid submission
is replayed unchanged in an isolated verifier. Delivery rejections preserve the
full original verdict, because grading returns before SQL in those cases.
Financial checks remain null for missing submissions. No extra artifact is
silently removed to repair delivery, and no missing answer is synthesized.

## Analytical findings

The accepted workpapers include different algebraic implementations of the
borrowing limit, acquisition cash classifications and liquidation allocations.
DeepSeek a01 passes despite terminating at the turn limit, demonstrating that
termination status alone does not determine financial correctness. Sol b02
passes all original and changed-input tests, including the strict trigger,
conversion ratios, ranking changes and unattained funding boundary.

DeepSeek b01 calculates every original and control table correctly. Its
performance-table citations are sufficient under the correction. Its other two
table citations remain incomplete: the acquisition table lacks Otezla proceeds
(s07), and cash coverage lacks the individual acquisition consideration and
acquired-cash disclosures (s01+s02). These are evidence failures, not numerical
failures. Citations supplied for other outputs do not automatically support an
uncited table.

GLM c01 calculates all tables and controls correctly. Its original failure was
the overly restrictive retained-interest citation rule. Sol c01 correctly
recasts cash flows and compares cash generation, but subtracts the 43 loss on
receivables sales as an additional DPP movement. It returns 535 explained and
+15 unallocated, against 578 and -28. The source separately reports a noncash
DPP addition of 7,682. The loss disclosure describes discounts at sale and does
not establish a further subsequent reduction of that recognized DPP addition.
The extra deduction assumes an unsupported mapping. The same numerical error
persists on all eight controls. The retained-interest definition could describe
its gross movement scope more explicitly in a future version. This wording
limitation is recorded rather than changing the executed question after review.

GLM a01, GLM b02 and DeepSeek b02 omit `answer.json`. GLM b02 also omits
`owner_funding.sql`. Their strict financial dimensions are unassessed. Static
review of the retained partial b02 SQL nevertheless identifies economically
meaningful defects. These examples are independently calculated implications
of the SQL, **not executed candidate outputs or additional scores**:

| Partial submission and frozen control | SQL-implied result, USD million | Correct result, USD million |
| --- | ---: | ---: |
| GLM, trigger raised to 3,000, Series A at proceeds 2,500 | 35.0004375 | 69.418725599348 |
| GLM, same control, Series B conversion frontier | 1,895.6826464693 | 2,242.0757867903 |
| DeepSeek, E conversion ratio 1.2, E frontier | 5,919.417969217 | 5,140.0815758769 |
| DeepSeek, A-1 promoted to senior rank, A-1 at proceeds 240 | 0 | 0.088308666497 |
| DeepSeek, mandatory trigger lowered to 120, A_4 funding boundary | 211.118590443368 | 1,848.906933308633 |
| DeepSeek, F target raised to 55, funding boundary | NULL | 243.114814715621, attained |

GLM forbids voluntary A/A-1 conversion below the mandatory threshold, although
conversion can pay more. Its alternate frontier omits original common shares
and retains preferences for already-converted shares. DeepSeek assumes a unit
conversion ratio, keeps A-1 junior after its rank changes, hardcodes the original
trigger, and misses an ordinary post-trigger funding branch. These controls
change disclosed rights consistently. They expose financial model assumptions,
not citation formatting. GLM's partial a01 collateral algebra appears valid,
but it does not receive a fabricated complete-submission result.

## Use and limits

The supplement provides four runnable evaluation packages and five separately
identified development tasks alongside the unchanged 30-task v15 suite. Use the
[execution guide](../../docs/WORKFLOW_HARD_EVALUATION.md) and report this
supplement separately from v15. All four financial source groups differ from
those in development. Financial task content was not tuned after final trials.

The observed outcomes support using these cases to examine financial modeling,
recomputation, evidence selection and completion under declared agent conditions.
They do not isolate model intelligence from agent scaffolding or output limits,
and they do not establish a Terminal-Bench-equivalent difficulty scale. The
four-task sample, one attempt per configuration/task and public references limit
generalization. Independent human financial/source review and actual external
user testing remain pending. Current packages have deterministic financial,
alternative-solution, control, isolation and supported-native-path verification.

Across the eight delivered workpapers, all 24 original-dossier claim verdicts
are correct. Seven workpapers pass every numerical table and control, and one
has the retained-interest error described above. Four slots have no valid full
delivery. This decomposition matters: the strict completion counts combine
financial correctness, evidence selection and successful delivery. They are not
pure financial-reasoning pass rates.
