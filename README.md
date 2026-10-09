# WorkpaperBench

**Can a financial-research agent repair a workpaper, support its conclusions, and keep it correct when the inputs change?**

WorkpaperBench turns public financial disclosures and flawed starting SQL into
inspectable research tasks. A submission contains three SQL queries and a JSON
file with evidence and claim verdicts. Deterministic, isolated verification tests
financial reasoning, source selection, reconciliation, and robustness.

The contribution is a benchmark that separates a plausible answer from a
reproducible work product - and separates financial mistakes from grader mistakes.

**Current software: workflow-v6, scorer workflow-1.2.0.** Thirty source-backed
cases, six development and 24 evaluation. Authored references and controls are
verified. No model has been evaluated on these revised tasks. Human review,
external replication, and leading-model discrimination remain unmeasured.

[Task](datasets/workflow-v6/tasks/c01/instruction.md) · [Methods](docs/WORKFLOW.md) · [Corrected replays](reports/workflow-v5/corrected-replay.json) · [Validation](reports/local/workflow-validity-suite.json)

## Try it without a model

From this checkout, using Python 3.12:

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
./wpb demo
./wpb validate examples/block-workpaper-v6/answer.json
```

The demo displays a reference calculation and recorded replay diagnostics. It
needs no account, model weights, or container. `validate` checks JSON structure
only. To run the regression suite:

```sh
.venv/bin/python -m pytest -q
```

To verify financial correctness, configure the dedicated Linux guest in
[local execution](docs/LOCAL.md#verify-a-workpaper-without-inference), then run:

```sh
./wpb grade --dataset workflow-v6 --task c01 \
  --artifacts examples/block-workpaper-v6 --attempt my-block-example-1
```

The example should pass every check. Use a fresh attempt ID for each run.
Verification needs no inference server. The tested wrapper uses Lima on the
Intel Mac Pro, with Docker inside the separate Linux guest. Other platform
combinations have not been validated. [Reproduction commands](docs/WORKFLOW.md#reproduce-the-quality-checks)
cover catalog reconstruction, controls, and exact retained-artifact replay.

## One concrete financial distinction

Block's FY2024 Bitcoin revenue increased by USD 700.903 million, while
consolidated revenue increased by USD 2,205.430 million. Bitcoin's contribution
to total revenue growth is:

```text
100 × (10,199,205 − 9,498,302) / (24,121,053 − 21,915,623) = 31.7808%
```

A change in Bitcoin's share of annual revenue, −1.0569 percentage points, answers
a different question. Reporting the ratio as 0.3178% introduces a 100-fold unit
error. The task also requires a signed gross-profit bridge, reconciliation, and
a verdict on whether higher Bitcoin prices caused most of Bitcoin revenue growth.
The supplied totals alone cannot establish that causal claim.

Follow the [source dossier](datasets/workflow-v6/tasks/c01/environment/sources.md),
[public contract](datasets/workflow-v6/tasks/c01/environment/output_contract.json),
and [example SQL](examples/block-workpaper-v6/revenue_bridge.sql).

## What the tasks test

| Family | Research work | Development / evaluation |
| --- | --- | ---: |
| Update a model | Reconstruct quarters, repair definitions, preserve valid periods | 2 / 8 |
| Audit a metric | Fix denominators, duplicates, units, and stock/flow errors | 2 / 8 |
| Explain a change | Build signed bridges, reconcile bases, bound causal attribution | 2 / 8 |

Each task declares columns, keys, units, tolerances, label aliases, and three
claim assertions. Supported means the evidence entails the assertion,
contradicted means it entails its negation, and unresolved means neither follows.
Twenty cases have no unresolved claim, ten have one, and its position varies.
A fixed uncertainty answer is no longer guaranteed a correct claim in every case.

Reports separate **numerical tables, claim verdicts, evidence, robustness, and
delivery**. Table diagnostics distinguish numeric mismatches from missing columns,
keys, rows, or failed SQL. Source IDs may appear inside explanations. Declared
source-label aliases and equivalent SQL are accepted. Swapped categories, wrong
units, unrelated citations, and duplicate keys remain failures.

SQL runs against pristine inputs in a separate networkless verifier with bounded
time, memory, and output. Candidates cannot access gold, repository history,
credentials, or privileged sockets. Synthetic controls alter observations,
introduce duplicate exports and irrelevant periods, and break accidental
zero-residual shortcuts. [Isolation evidence](reports/local/local-boundary-validation.json)
and [current controls](reports/local/workflow-validity-suite.json) are software
validation, not model accuracy measurements.

## What has actually been measured

These are **corrected replays of three retained workflow-v5 development
workpapers**, using scorer 1.2.0 and unchanged JSON/SQL bytes:

| Workpaper | Numbers | Claims | Evidence | Robustness | Delivery |
| --- | --- | --- | --- | --- | --- |
| Block | Pass | Pass | Pass | Pass | Pass |
| Microsoft | Fail | Pass | Pass | Fail | Pass |
| Brale | Pass | Pass | Pass | Fail | Pass |

Block's original failure came from full filing labels versus shortened reference
labels. Microsoft's source IDs embedded in explanations now receive credit,
but its −11,262.74 basis-point calculation still fails against −112.63. Brale
still fails to deduplicate identical exports. Ambiguous historical claims accept
both defensible verdicts in these replays. Revised tasks have one explicit verdict.

[Original files and receipts](reports/workflow-v5/submissions) remain inspectable
beside the [correction report](reports/workflow-v5/corrected-replay.json).
These Qwen3.6-35B-A3B UD-Q5_K_M attempts used different development budgets and
settings, including a continued Block session. They are not a controlled model
comparison. Earlier failures remain in the [original pilot](reports/local/workflow-qwen36-development-1.json)
and [recovery record](reports/local/workflow-qwen36-development-5.json).
The separate [historical hosted study](reports/challenge-v1/reviewed-results.md)
is preserved. None of these results measures workflow-v6 performance.

## Limits and contribution

Public disclosures, repeated issuer templates, and public reference answers create
contamination risks. The 24 evaluation source groups do not overlap development
groups, but this is not a private test set. They have received trusted control
validation only. Evidence grading checks reviewed source selections, not free-text
entailment. Finite synthetic controls do not prove correctness on every future
input. Claim-label accuracy alone does not establish calibrated abstention.

A useful contribution is a valid workpaper rejected by the grader, an independently
checked reference, or a failing financial counterexample. Include the task and
scorer IDs, submitted files, expected result, and supporting source. Grader fixes
receive new identities rather than overwriting old results.

Code is [MIT licensed](LICENSE). [Source rights and provenance](DATA_SOURCES.md)
distinguish public observations, authored defects, synthetic controls, reference
answers, and actual submissions. 