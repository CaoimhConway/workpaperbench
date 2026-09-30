# WorkpaperBench

**Can a research agent repair a financial workpaper, support its conclusions, and keep it correct when the inputs change?**

WorkpaperBench turns public financial disclosures and flawed starting SQL into
verifiable research tasks. Each submission is a small, inspectable work product:
three SQL tables and a JSON file containing source references and claim verdicts.
A separate verifier checks the numbers, evidence, behavior on changed inputs,
and delivery. No model judges the answers.

[Try the demo](#try-it-without-a-model) · [Inspect a task](datasets/workflow-v5/tasks/c01/instruction.md) · [Methods](docs/WORKFLOW.md) · [Validation](reports/local/workflow-quality-suite.json) · [Historical results](reports/challenge-v1/reviewed-results.md)

**Current release: workflow-v5, scorer workflow-1.1.0.** Thirty source-backed cases,
six development and 24 evaluation. Software and authored controls are verified.
Candidate-model evaluation on the 24 evaluation cases, human review, and external
replication remain pending. This is a research prerelease, with a separately
preserved measured regression study.

Engineering checks: **413 tests**, **117 isolated controls**, and native reference
and replay verification.

## A correct-looking answer can measure the wrong thing

Block's FY2024 filing reports Bitcoin revenue increasing from $9.498 billion to
$10.199 billion, while consolidated revenue increases from $21.916 billion to
$24.121 billion. The question is how much Bitcoin contributes to total revenue growth.

| Workpaper | Result | What it measures |
| --- | ---: | --- |
| Authored reference | **31.7808%** | Bitcoin revenue increase / total revenue increase |
| Retained model submission | **−1.0569** | Change in Bitcoin's share of annual revenue |
| Another retained submission | **0.3178%** | Correct ratio, wrong percent scale |

The [original filing](https://www.sec.gov/Archives/edgar/data/1512673/000162828025007376/sq-20241231.htm),
[retained answers](reports/runs/challenge-v1-evaluation-d9a2fe13f6f2), and
[authored workflow example](examples/block-workpaper) make the distinction inspectable.
The workflow task also requires a gross-profit bridge, signed amortization,
reconciliation, and an explicit limit on what the disclosure says about Bitcoin prices.

## Try it without a model

Python 3.12 is the tested version. The demo needs no account, model weights, or container.

```sh
git clone --branch v0.5.0-local.2 https://github.com/CaoimhConway/workpaperbench.git
cd workpaperbench
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
./wpb demo
./wpb validate examples/block-workpaper/answer.json
```

The demo shows the reference beside actual historical submissions. `validate`
checks JSON structure only. Open the [task request](datasets/workflow-v5/tasks/c01/instruction.md),
[source dossier](datasets/workflow-v5/tasks/c01/environment/sources.md),
[output contract](datasets/workflow-v5/tasks/c01/environment/output_contract.json),
and [example SQL](examples/block-workpaper/revenue_bridge.sql) to follow the calculation.

For financial verification, set up the dedicated Linux guest in
[local execution](docs/LOCAL.md#verify-a-workpaper-without-inference), then run:

```sh
./wpb grade --dataset workflow-v5 --task c01 \
  --artifacts examples/block-workpaper --attempt block-example-1
```

This example should pass all four checks. Substitute your own artifact directory
to assess a repair. Each attempt gets a fresh receipt with task, scorer and artifact
hashes. Reusing an attempt ID is rejected. Grading requires no inference server.
[Replay and reporting](docs/LOCAL.md#submit-replay-and-report) preserve the original
artifacts and verify them again from pristine inputs. The shipped example and
its fresh replay are [recorded here](reports/local/workflow-example-replay.json).

## What the tasks test

| Family | Work required | Examples | Development / evaluation |
| --- | --- | --- | ---: |
| Update a model | Reconstruct periods, repair definitions, preserve valid outputs | Microsoft quarters, Circle expense definitions, Nvidia H20 adjustments | 2 / 8 |
| Audit a metric | Fix denominators, duplicates, units and stock/flow errors | Stablecoin reserves, Coinbase activity, Airbnb trailing cash flow | 2 / 8 |
| Explain a change | Build signed bridges, reconcile bases, bound attribution | Block revenue, Cisco revised accounts, JPMorgan significant items | 2 / 8 |

Every task has three named result tables, three structured claims, and declared
keys, units and tolerances. The [30-case catalog](datasets/workflow-v5/manifest.json)
records the split and source groups. The 24 evaluation source groups do not overlap
the six development groups. Related issuer templates can still overlap, and the
public tasks are not a contamination-proof test set.

## How a workpaper earns a pass

| Diagnostic | Requirement |
| --- | --- |
| Financial answer | All original table values and claim verdicts are correct |
| Evidence | Each output has sufficient, relevant support, including accepted alternatives |
| Preservation | SQL remains correct on synthetic changes and preserves unaffected outputs |
| Delivery | Exactly the requested JSON and bounded SQL files are submitted |

[Scorer](config/scorers/workflow-1.1.0.py) · [Catalog builder](scripts/build_workflow_quality.py) · [Control sweep](scripts/validate_workflow_quality.py)

Version 5 closes two grader shortcuts. Citing every source no longer substitutes
for selecting relevant evidence. Fifty-one residual columns now encounter
independently changed observations, so a hard-coded zero fails even if it matches
the original disclosure. Three residuals that were zero by algebraic construction
were removed. Valid alternative SQL, row and column order, and relevant additional
citations are tested as positive controls.

Verification runs read-only SQL against pristine data in a separate networkless
container with time, memory and output limits. The candidate receives neither
gold nor repository history. [Boundary tests](reports/local/local-boundary-validation.json),
[prototype checks](reports/local/workflow-quality-prototypes.json), and
[suite checks](reports/local/workflow-quality-suite.json) retain actual evidence.
These are software checks using authored submissions, not model accuracy scores.

## What has actually been measured

The historical challenge-v1 study evaluated nine tasks, three attempts per task,
on each of two hosted profiles. Under corrected scorer challenge-1.1.3:

| Historical profile | Financial correctness | Complete workpaper |
| --- | ---: | ---: |
| Inexpensive | 17 / 27 | 8 / 27 |
| Reference | 25 / 27 | 18 / 27 |

[The reviewed report](reports/challenge-v1/reviewed-results.md) contains model
identities, per-task outcomes, scorer corrections and limitations. These 27
attempts per profile are clustered within nine tasks, not 27 independent problems.
They do not establish accuracy on workflow-v5.

Local workflow-v4 calibration used Qwen3.5-9B Q4_K_M on three development prototypes.
One attempt delivered a workpaper: its original tables passed, while a claim and
duplicate-export checks failed. Two attempts produced partial files and were
unassessed for financial correctness. [All three outcomes](reports/local/workflow-development-budget-1.json)
remain visible. No leading-model comparison has been run on the new workflow suite.

## Reproduce, inspect, improve

- **Evaluation engineers:** run the [isolated control sweep](docs/WORKFLOW.md#reproduce-the-quality-checks), inspect scorer errors, or submit a competing workpaper.
- **Financial researchers:** start with the [blinded review pack](reports/local/human-review-pack.md). Human agreement has not yet been measured.
- **Contributors:** include the task and scorer IDs, exact submitted files, and a source-backed explanation when reporting a valid answer the grader rejects.

Code is [MIT licensed](LICENSE). [Source rights and provenance](DATA_SOURCES.md)
separate public observations, authored defects, synthetic controls and reference
answers. Complete restricted issuer captures are not redistributed.
