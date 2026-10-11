# Methodology and correction policy

WorkpaperBench measures bounded financial analysis over frozen evidence dossiers.
The default construction catalog has six development and 24 evaluation cases
across updating a model, auditing a metric and explaining a change. The separate
maintenance condition supplies existing queries to check and repair.
[Workflow methods](WORKFLOW.md) define the current task, claim and evidence
contracts and compare the two tracks.

## What completion means

A complete workpaper delivers the requested JSON and SQL files, calculates every
requested table correctly, cites sufficient evidence, assesses bounded claims
and recomputes correctly under synthetic controls. Alternative SQL is accepted
when its observable results agree. Row and column order do not matter. Declared
keys, units, aliases and absolute tolerances remain part of the public contract.

Numerical correctness, claim verdicts, evidence, robustness, delivery and
infrastructure are separate diagnostics. Missing or rejected deliveries leave
financial outcomes unassessed. An unexecuted check is `null`. A correct conclusion
with insufficient citations is distinguishable from an incorrect verdict.
Source-ID checks test source selection, not the truth of arbitrary explanatory
prose. Changed-input controls test selected invariants, not every possible input.

References are calculated independently from source observations using exact
decimal and date arithmetic. Source facts, normalized tables, authored defects,
synthetic controls, reference workpapers and actual submissions retain distinct
identities. Controls and repetitions add no independent observed datasets.
See [source provenance and rights](../DATA_SOURCES.md).

## Execution and reporting

Native Harbor/Hermes runs candidates in isolated environments with explicit
endpoint configuration and bounded execution. A separate Linux verifier receives
pristine inputs, no inference key and no network. Read-only SQL authorization,
bounded workers, resource limits and fresh state provide complementary controls.
Structural rejection prevents SQL execution. Candidate Python is not replayed.
The [execution guide](RUNNING.md) describes the actual credential boundary:
candidate terminal tools can read the key used by the native runtime.

Receipts bind attempts to catalog, task, scorer, runtime, submitted files and
configuration hashes. Reports preserve the declared schedule, missing attempts,
infrastructure failures and assessed coverage. Repetitions and shared source
groups are reported as such. Construction results cannot inherit maintenance
repair or preservation baselines. Budgets, continuation history and unscored
attempts accompany interpretation. Setup smokes and scripted protocol fixtures
are engineering checks, not measured model performance.

## Versioning and corrections

Every scored condition has its own immutable identity. Changes to questions,
source inputs, reference contracts or treatment require a new identity. Original
submissions and verdicts are preserved. A grading correction writes a separate
review result with its scorer version, implementation hash and exact input hash.
Reports show original and corrected diagnostics separately and reject mixed
conditions. Corrections never repair an official submitted answer.

The [workflow validity record](WORKFLOW.md#validity-revisions-and-continuity)
documents evidence alternatives, residual controls and claim revisions. Historical
maintenance results remain attached to their original catalogs. Reviewed replay
is inference-free and does not establish performance on a new catalog.

The original eight-task manifest and the separate `real-v1` manifest retain their
published execution identities. Explicit operational receipts permit key-free
inspection and reconstruction with reviewed code. The
[publication-input registry](../config/publication-inputs.json) separately binds
neutral historical context copies to original input hashes. Source tables,
reference answers, evidence IDs, targets, tolerances and control databases remain
fixed. Public copies have separate byte hashes. Withheld historical tool excerpts
retain original-content digests and omission metadata. They are not presented as
newly observed output.

Original paid-launch freeze checks remain strict. A publication receipt does not
authorize inference or silently refresh a historical campaign. A new measured
experiment requires a new manifest and retains every scheduled attempt and
failure. Historical scores, costs and assessed coverage remain unchanged.

## Interpretation limits

The benchmark supplies normalized observations, excerpts and definitions. It
does not measure open-web retrieval, source extraction, investment judgment,
cryptographic verification or confidence calibration. Public source history and
published references constrain contamination claims. Source-group separation
does not make related issuer templates independent.

The current construction condition has no reported model-performance result.
Historical small studies and local configurations cannot establish frontier
rankings. Evidence grading accepts reviewed support sets, with valid rejected
paths treated as grader defects. Claim-label priors, bounded controls and
disclosed assistance limit the inference drawn from completion scores. Human
agreement and external validation require their own evidence.
