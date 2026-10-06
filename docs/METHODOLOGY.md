# Methodology and correction policy

## Active real-v1 study

`datasets/real-v1/manifest.json` defines a new experiment identity, source/task hashes, reference answers, scorer/runtime, routing, treatment, schedule and cumulative budgets. All manifest fields are canonically hashed, excluding only the two identity/hash fields. Changing inputs and rehashing them cannot preserve the old identity. The original `config/freeze.json`, correction registry, candidate packages and results remain historical.

Post-release operational fixes are recorded in `datasets/real-v1/operations-review.json`, bound to the exact published manifest bytes. Key-free reconstruction, publication audit and fresh replay accept only the explicitly listed operational code hashes. Candidate inputs, source captures, references, scorer, model, treatment and schedule keep their original hashes. Paid execution checks the original freeze without consulting this receipt, so the corrected checkout cannot relaunch the published campaign. The failed Apple B1 slot and 47/48 retained coverage remain part of that campaign.

The suite has six real-source base tasks and two synthetic diagnostic tasks. All changed-input controls are synthetic counterfactuals. The Bitcoin transaction pages are predeclared first-25 samples, not whole-block datasets. Matched coverage for the fee-rate task means actual transaction versions present in both samples, with coinbase excluded. This does not match individual transactions or establish instrumentation changes. Circulating stablecoin quantities, reserve USD fair values, fees, output values and market valuation are different metrics.

The evidence contract is per claim, declared in every candidate instruction before freeze. Cite the observed operands and metric definition, with relevant scope evidence allowed. Relevant timing and scope records are accepted equivalent context. A bounded conclusion cites the relevant calculation or scope evidence. There is no hidden task-specific citation repetition rule or answer-revealing reason vocabulary. Official outputs are never repaired. Scorer 1.2.0 is reused unchanged, while the new task/reference/control hashes give this suite its own scoring identity.

Development uses real-v1-wp01/wp02/wp05. Evaluation uses wp03/wp04/wp06/wp07/wp08. The intervention and model are reused. At most six compatibility/pilot attempts are authorized, with two declared pilot slots in this snapshot. The final schedule is 48 slots. No evaluation output informs treatment tuning. Shared source groups never cross the split. Previously exposed filing and diagnostic cases are regression tests, not newly unseen tasks.

Reporting preserves scheduled counts, assessed numerical/conclusion/evidence/replay counts and retained-answer coverage. Missing citations or reason codes are distinct from incorrect financial conclusions. New and historical study scores are never pooled. Repeated attempts and shared Bitcoin pages do not create independent datasets.

Fresh [replay](REPLAY.md) executes the native separate verifier for selected retained bytes or a bounded committed engineer answer, writing immutable run/input/task/scorer receipts and comparing prior diagnostics without replacing them. Cached historical regrading is separately labeled. All submitted SQL remains Actions-only. Local tests execute only trusted authored controls and reference SQL.

The preflight reads provider lifetime metadata without inference. Paid runs preserve the lower dedicated cap of USD 20 within the USD 50 project ceiling, including historical spend. Standard public Linux Actions compute is free under the current runner route. Storage/account invoices are still unknown, with the USD 10 incremental project Actions limit unchanged.

## Historical study and reviewed scoring

WorkpaperBench measures bounded financial work over supplied tables and evidence. It does not measure open-web retrieval, general investment judgment or cryptographic verification.

## What passes

A task is complete only when every requested answer has the right value, unit, supporting evidence and availability decision, its SQL recomputes correctly, and any requested conclusion is supported. Correct JSON alone is not enough. Neither is a correct scalar.

The reviewed scorer accepts ordinary safe SQLite arithmetic, CTEs, joins, subqueries and aggregates. Its bounded function set includes `sum`, `total`, `count`, `min`, `max`, `avg`, `round`, `abs`, `coalesce`, `ifnull`, `nullif`, `lower`, `upper`, `length`, `substr`, `substring`, `trim`, `ltrim`, `rtrim`, `replace`, `instr`, `typeof`, `iif`, `like` and `glob`. Window functions such as `row_number`, `rank`, `lag`, `lead`, `first_value` and `last_value` are supported under the same resource limits. Date/time functions accept explicit text or numeric values: `date`, `time`, `datetime`, `julianday`, `unixepoch` and `strftime`. Wall-clock defaults, `now`, timezone-dependent modifiers and implicit-current-time subsecond forms are rejected. Writes, attached databases, extensions and arbitrary candidate Python remain prohibited.

Read-only inputs, an authorizer, a bounded subprocess, resource limits and a native separate verifier are complementary controls. A statement-prefix check is not the security boundary.

## Independent diagnostics

Strict format failures still fail the task. Uniquely identifiable requested answers can nevertheless be inspected without repairing the submission. Extra claims do not erase a correct requested number. Duplicate requested claims are not resolved by picking a favorable one.

The reviewed scorer records numerical correctness, units, source-ID requirements, availability, original replay, changed-input replay, and conclusion verdict/reason/evidence separately. A correct conclusion with a missing citation is not reported as a wrong conclusion verdict. An unexecuted check is `null`, not a failure. Evidence requirements are reviewed task-local contracts, not an automatic proof of arbitrary prose.

## Frozen experiment versus reviewed scoring

`config/freeze.json` remains the original, immutable experiment manifest `wpb-v1-92baa4a72f0e`. Its execution snapshot is commit `b4e256dc8976223a8a3fdad157a6b212f49bb8e1`, and its completed run is `37280454673`. The review changes neither its candidate inputs, model, skill nor historical jobs.

`config/review.json` hashes the correction implementation. The publication audit separately checks that original candidate-facing inputs are unchanged. Original records and verdicts are never overwritten. Native, inference-free rescoring of retained answers writes `regrade.json`, identifying scorer version, code hash, input hash and Actions run. Results show original and reviewed scores separately. Repeating a review with the same scorer and input is a no-op. A changed review preserves the prior sidecar under its content hash. A report cannot silently mix scorer versions.

The working tree intentionally no longer matches every code hash of the old execution snapshot. Dispatching a new paid final campaign under that old freeze fails closed. Reproduce the old implementation from its commit. Any new scored experiment requires an explicitly new immutable manifest, not a silent refresh of old hashes or retries selected for better scores.

The correction registry authorizes publication of reviewed code, never paid execution under the old freeze. The launcher checks every original frozen hash without consulting that registry. Attempt receipts and new imports use experiment/slot directories. Published legacy evidence keeps its flat paths. Collection authenticates each named attempt against Actions metadata, including earlier attempts when a run has since been rerun.

## Attempts, ordering and missing data

New workflows identify trials by experiment plus slot, reject same-run reruns, and recheck history before installation. An older Actions run retains its original workflow definition, so these protections cannot retrofit a rerun of the legacy campaign. Never rerun that original run. Receipts in new workflows are written before setup and incomplete receipts become infrastructure failures. Reconciliation distinguishes queued, running, missing-artifact and completed states. Missing evidence is never fabricated.

Both arms for one task/repetition execute in declared order inside one short-lived job, with fresh native environments for each arm. Pairs run serially. The order between pairs remains scheduler-dependent and is recorded, not assumed. The original campaign used a serial matrix without this within-pair guarantee, so its actual order must be inspected rather than retroactively relabeled.

New valid and malformed answers retain bounded, credential-screened original bytes, with a separate digest for normalized JSON. Escaped credential patterns are checked before retaining either. Legacy raw bytes discarded by the original runner cannot be recovered from a hash. Artifact audits identify normalized-only or unavailable originals. New retention includes up to 25 screened invocations and 25 screened observations, each at most 8,000 encoded bytes, excluding assistant messages. Omitted items are counted. The original campaign retained tool counts only. Its raw trajectories and observations are unavailable, so this release makes no retrospective claim to possess them. Pattern screening catches known credentials and several common encodings but cannot guarantee that arbitrary obfuscation or private content is safe.

## Limits that matter

Eight tasks, one model, one intervention and three attempts per arm are a small engineering study. Five evaluation tasks are not five independent datasets. Two filing tasks use public facts, the other six cases are synthetic, and two share the same fallback corpus. Some evidence-limit tasks are explicitly cued by supplied scope notes. Changed-input controls expose selected mistakes, not all possible programs. Provider routing and upstream installation dependencies retain disclosed variability. Per-slot cost snapshots can lag and are not exact A/B cost allocations.

## Results publication

The key-free CI workflow collects the requested existing campaign, checks native controls and regrades retained answers without inference. It emits screened results as downloadable artifacts. Repository maintainers inspect those artifacts before committing or publishing them. No workflow writes source or Git identity. These operations do not launch, repeat or repair model answers.

## Scorer 1.2.0

The correction forbids SQL execution whenever structure is rejected. Only uniquely identifiable requested numerical claims are then assessed. Safe explicit-date, text and window alternatives still execute on both pristine fixtures under the existing 256 MiB Linux address-space limit, two-second CPU limit, 1.5-second progress deadline and two-second subprocess timeout. No resource limit was increased. Collection requires authenticated archive digests and validates schedule, run, attempt, commit and retained-file identities before replay. The correction registry allowlist cannot authorize candidate inputs, references, model, runtime, schedule or treatment changes. Original strict verdicts and prior 1.1.0 regrades remain historical evidence.


## Research Challenge related work

The new suite borrows design practices, not task questions, software stacks or historical scores. [Hermes ToolPerf](https://github.com/NousResearch/hermes-toolperf-evals) links sandbox cases to observed tool-error classes and retains tool traces. It motivates diagnosis of source selection, scope, calculation, evidence and infrastructure separately here, without claiming a financial product defect. No root redistribution license was identified, so no materials are copied.

[FinanceBench](https://github.com/patronus-ai/financebench/tree/cc39aeb4afdf33909ee1412188bf89035950c2eb) separates financial questions, source document/page evidence and justification. That motivates dossier source locators and claim-linked support. Its authors' manual review is not validation of this suite. No repository license was identified and no questions or source corpus are copied.

[FinQA](https://github.com/czyssrs/FinQA/tree/0f16e2867befa6840783e58be38c9efb9229d742) supplies executable arithmetic programs and supporting table/text facts. Its MIT repository and execution-versus-program checks motivate explicit reproducible calculations here. This suite uses constrained SQL with changed-input checks rather than program-token matching. Its documented earlier label leakage reinforces candidate-only leakage audits.

[Spider2](https://github.com/xlang-ai/Spider2/tree/cafb867313aab4e674652054198f383cf4018943) tests schema/document navigation and execution results in enterprise SQL workflows. Its MIT repository motivates ordinary dossier navigation and valid SQL alternatives. WorkpaperBench uses small offline SQLite inputs, with no Snowflake/BigQuery service or enterprise breadth claim. Dataset and external-source terms are separate from code licensing.

[Vals Finance Agent](https://github.com/vals-ai/finance-agent/tree/8ba65f81ab759a8e0d44e72aabc5a47cf839d563) uses web/EDGAR search and HTML retrieval and retains tool/token/error logs. Its MIT implementation motivates analyst-shaped requests and source-path observations. WorkpaperBench freezes evidence and grades deterministic financial propositions instead of depending on a live search service or a platform judge. The README does not document its platform scoring formula, so no scoring comparison is inferred.

The three development dossiers and their controls received a separate source-first review before exposure. Review status and actual validation are in BUILD_STATUS.md. No human validation or historical score comparison is claimed.
