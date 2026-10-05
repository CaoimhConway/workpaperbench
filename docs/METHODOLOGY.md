# Methodology and correction policy

WorkpaperBench measures bounded financial work over supplied tables and evidence. It does not measure open-web retrieval, general investment judgment or cryptographic verification.

## What passes

A task is complete only when every requested answer has the right value, unit, supporting evidence and availability decision, its SQL recomputes correctly, and any requested conclusion is supported. Correct JSON alone is not enough. Neither is a correct scalar.

The reviewed scorer accepts ordinary safe SQLite arithmetic, CTEs, joins, subqueries and aggregates. Its bounded function set includes `sum`, `total`, `count`, `min`, `max`, `avg`, `round`, `abs`, `coalesce`, `ifnull`, `nullif`, `lower`, `upper`, `length`, `substr`, `substring`, `trim`, `ltrim`, `rtrim`, `replace`, `instr`, `typeof`, `iif`, `like` and `glob`. Date/time functions accept explicit values: `date`, `time`, `datetime`, `julianday`, `unixepoch` and `strftime`. Wall-clock defaults, `now`, timezone-dependent modifiers and implicit-current-time subsecond forms are rejected. Writes, attached databases, extensions and arbitrary candidate Python remain prohibited.

Read-only inputs, an authorizer, a bounded subprocess, resource limits and a native separate verifier are complementary controls. A statement-prefix check is not the security boundary.

## Independent diagnostics

Strict format failures still fail the task. Uniquely identifiable requested answers can nevertheless be inspected without repairing the submission. Extra claims do not erase a correct requested number. Duplicate requested claims are not resolved by picking a favorable one.

The reviewed scorer records numerical correctness, units, source-ID requirements, availability, original replay, changed-input replay, and conclusion verdict/reason/evidence separately. A correct conclusion with a missing citation is not reported as a wrong conclusion verdict. An unexecuted check is `null`, not a failure. Evidence requirements are reviewed task-local contracts, not an automatic proof of arbitrary prose.

## Frozen experiment versus reviewed scoring

`config/freeze.json` remains the original, immutable experiment manifest `wpb-v1-92baa4a72f0e`. Its execution snapshot is commit `b4e256dc8976223a8a3fdad157a6b212f49bb8e1`, and its active run is `37280454673`. The review changes neither its candidate inputs, model, skill nor already running jobs.

`config/review.json` hashes the correction implementation. The publication audit separately checks that original candidate-facing inputs are unchanged. Original records and verdicts are never overwritten. Native, inference-free rescoring of retained answers writes `regrade.json`, identifying scorer version, code hash, input hash and Actions run. Results show original and reviewed scores separately.

The working tree intentionally no longer matches every code hash of the old execution snapshot. Dispatching a new paid final campaign under that old freeze fails closed. Reproduce the old implementation from its commit. Any new scored experiment requires an explicitly new immutable manifest, not a silent refresh of old hashes or retries selected for better scores.

## Attempts, ordering and missing data

New workflows identify trials by experiment plus slot, reject same-run reruns, and recheck history before installation. Receipts are written before setup and incomplete receipts become infrastructure failures. Reconciliation distinguishes queued, running, missing-artifact and completed states. Missing evidence is never fabricated.

Both arms for one task/repetition execute in declared order inside one short-lived job, with fresh native environments for each arm. Pairs run serially. The order between pairs remains scheduler-dependent and is recorded, not assumed. The original campaign used a serial matrix without this within-pair guarantee, so its actual order must be inspected rather than retroactively relabeled.

New valid and malformed answers retain bounded, credential-screened original bytes, with a separate digest for normalized JSON. Escaped credential patterns are checked before retaining either. Legacy raw bytes discarded by the original runner cannot be recovered from a hash. Artifact audits identify normalized-only or unavailable originals. Small screened tool-invocation records exclude assistant messages and do not claim a complete trajectory.

## Limits that matter

Eight tasks, one model, one intervention and three attempts per arm are a small engineering study. Five evaluation tasks are not five independent datasets. Two filing tasks use public facts, the other six cases are synthetic, and two share the same fallback corpus. Some evidence-limit tasks are explicitly cued by supplied scope notes. Changed-input controls expose selected mistakes, not all possible programs. Provider routing and upstream installation dependencies retain disclosed variability. Per-slot cost snapshots can lag and are not exact A/B cost allocations.
