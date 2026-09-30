# Workflow methods

The current catalog is `workflow-v5-canonical-7429612183c6`, using scorer
`workflow-1.1.0`. It contains six development and 24 evaluation cases.
Each case requests three SQL result tables and three structured claim verdicts.
The deliverable is `answer.json` plus its three named `.sql` files.
The [Block example](../examples/block-workpaper) is an authored reference, not a model submission.

## Measurement contract

Financial correctness requires every requested original row and claim verdict.
Rows are matched by declared keys, columns by name, and numeric values by explicit
absolute tolerances. Correct row and column permutations are accepted. Different
SQL is accepted when its observable results match on both original and control
inputs. Three to five synthetic controls per task test specific dependencies,
not correctness on every possible future input.

Evidence is checked separately for each table and claim. At least one reviewed
support set must be present. Extra citations are accepted when they belong to a
reviewed alternative or supply relevant context for that output. Empty support,
invented IDs and unrelated sections fail. This checks structured source selection,
not entailment of arbitrary prose. Source granularity and the reviewed set of
alternatives can still cause false rejections. A valid rejected source path is a
grader defect to review and version, not evidence of model reasoning failure.

Preservation requires correct recomputation across all controls. Claims refer to
the original dossier only. Delivery requires the requested files, bounded size,
unique IDs and safe relative filenames. Structural rejection prevents SQL replay.
Well-formed partial claims may receive separate diagnostics, but missing outputs
remain unassessed and cannot count as completed workpapers.

The three claim labels across the catalog are 27 supported, 33 contradicted and
30 unresolved. Every case includes an unresolved attribution boundary. This
structure is a known shortcut for guessing uncertainty labels, so claim-label
accuracy alone does not demonstrate calibrated abstention. Full completion also
requires numerical work, evidence and preservation. Future calibration claims
require independently designed answerable/unanswerable pairs and human review.

## Quality revision and continuity

Version 4 accepted all known evidence IDs as shared context, which let blanket
citation pass. Version 5 uses [reviewed per-output context](../config/workflow-quality-review.json)
and preserves the previously accepted sufficient support alternatives.

The audit found 54 residual columns that stayed zero across all existing inputs.
Fifty-one compare independently supplied quantities. New synthetic discrepancies
change individual observed amounts without forcing reported totals to agree.
Independent Decimal reference calculations supply expected results. A submission
that replaces these residuals with zero matches the originals but must fail the
new controls. These inputs deliberately represent inconsistent disclosures or
extractions. They are not claims that an issuer published the counterfactual.

Two Microsoft Q1 + Q2 - H1 residuals and one Alphabet constructed bridge residual
were identities. They were removed from the public contract, reference outputs
and corresponding starting queries. Their useful underlying calculations remain.
The new Costco control also exposed a disagreement between the independent
calculator and reference SQL. The operating-growth denominator now explicitly
uses the duration-matched reported operating-income change. The independent
calculator was corrected for the new control, without changing original values.

All authentic source observations, prior synthetic databases and other starting
SQL remain byte-identical to version 4. Claims, prior financial values and prior
controls retain their original meaning. The builder and regression tests enforce
this boundary.

This is an additional task-quality revision authorized on 12 October 2026, after
the earlier one-revision local calibration protocol had ended. It is not part of
that frozen model study. The old releases and calibration receipts retain their
original catalog and scorer. No workflow-v4 model score is relabeled as version 5.

## Reproduce the quality checks

The [local execution guide](LOCAL.md) configures a separate Ubuntu 24.04 guest.
No model or inference server is needed for these checks.

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/build_workflow_quality.py --check
.venv/bin/python scripts/validate_workflow_quality.py \
  --native-prefix my-quality --output /tmp/my-quality-prototypes.json
.venv/bin/python scripts/validate_workflow_quality.py \
  --tasks all --output /tmp/my-quality-suite.json
```

Use fresh output paths and attempt prefixes. The first validation command runs
Microsoft, Brale and Block through native Harbor and then exercises their separate
verifiers. The second sweeps all 30 task verifiers using fresh containers. Each
case receives a correct reference, an alternative with reordered SQL and relevant
context, and a blanket-citation submission. The 27 applicable cases also receive
SQL that forces the originally zero residuals to remain zero.

Every verifier container has network-none, a read-only root, temporary bounded
artifact storage, no capabilities, no inference credential and no Docker socket.
SQL executes only inside the isolated Linux verifier. Actual network/namespace
checks are retained with every verdict. These controls complement the earlier
[resource and candidate-boundary probes](../reports/local/local-boundary-validation.json).
They do not constitute a security proof for arbitrary workloads.

Published verification includes [the complete 30-case sweep](../reports/local/workflow-quality-suite.json)
and [three prototype checks through native Harbor](../reports/local/workflow-quality-prototypes.json). Receipts record task, scorer, image and artifact hashes,
individual table/claim results, and expected failures. Three reference submissions
also traverse native Harbor. The sweep calls the same frozen verifier entry point.
It does not count container checks as model trials or as native agent trajectories.

## Evaluation and source limits

The evaluation split has 24 distinct source-window groups without development
group overlap. The source windows were selected and authored by the benchmark
builder. Public source documents, related issuer templates, public reference code
and repeated task structure create potential contamination and shortcut risks.
Held out means not used for candidate-model tuning in this project, not private
or guaranteed absent from model training.

Observed facts, normalized tables, authored starting-query defects, synthetic
counterfactuals, references and model submissions have different provenance.
Publication date, signature date, economic period and retrieval time must not be
interchanged. Primary-source captures and numerical derivations were reviewed
in the [source audit](../reports/local/workflow-source-review.json), but independent
financial-domain review is pending.

A future measured comparison needs frozen profiles and budgets, all scheduled
outcomes including failures, task-level paired reporting and uncertainty that
respects repeated attempts within a task. The current
[comparison configuration](../config/future-comparison.json) is disabled.
No current result supports a workflow leaderboard, frontier discrimination claim,
human agreement rate or general financial-research accuracy estimate.
