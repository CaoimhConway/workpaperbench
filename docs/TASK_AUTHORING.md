# Task authoring

The default suite is `workflow-v9`, the construction track with 30 tasks and
scorer `workflow-1.2.0`. Each task requests three SQL result tables and three
claim verdicts. Candidates receive observations and an output contract, with no
starting SQL. The six development and 24 evaluation cases have separate source
groups. The [methods](WORKFLOW.md) describe the measurement contract and splits.

Author new cases in a distinct future dataset directory. Keep published catalogs,
task IDs and frozen packages unchanged. New source observations, task requests or
grading rules require distinct task and catalog identities before evaluation.
The `workflow-v7` maintenance track is a separate condition with starting queries,
not an interchangeable source of construction results.

## Package and output contract

Use [construction task c01](../datasets/workflow-v9/tasks/c01/) and its
[candidate request](../datasets/workflow-v9/tasks/c01/instruction.md) as a concrete
package example:

| File | Responsibility |
| --- | --- |
| `instruction.md` | Financial question, task ID, output location and candidate requirements |
| `environment/data.sqlite` | Normalized source observations available to the candidate |
| `environment/sources.md` and `evidence.json` | Source excerpts, dates, definitions, provenance and evidence locators |
| `environment/schema.json` | Structure of `answer.json` |
| `environment/output_contract.json` | Requested tables, columns, keys, units, labels and claim assertions |
| `task.toml` and `environment/Dockerfile` | Native Harbor resources, candidate image and separate verification policy |
| `authoring.json` | Source group, split, reference method and control rationale |
| `solution/solve.sh` and three reference `.sql` files | Authored oracle submission |
| `tests/` | Pristine observations, synthetic controls, reference JSON, gold targets and isolated verifier |
| Dataset `manifest.json` | Catalog and task identities, source-group splits and frozen hashes |

Deliver `answer.json` and the three named `.sql` files to `/logs/artifacts`.
The JSON contains `task_id`, three `tables` entries and three `claims` entries.
Each table entry names its SQL basename and supporting evidence. Each claim
entry supplies its verdict and supporting evidence. Include every requested ID
exactly once and no extra files. SQL is read-only SELECT/CTE, separate from JSON.
The public schema and output contract specify names and limits.

Claim verdicts are `supported`, `contradicted` or `unresolved`, scoped to the
supplied dossier. Distinguish an absent disclosure from an unknown economic
quantity. Missing information is not zero. Evidence IDs must be known, relevant
and sufficient for each output. Explanations do not substitute for citations or
correct calculations.

## Source, reference and control checks

For each new case:

1. Record authentic source locators, observation periods, units, publication
   precision and redistribution rights. Label authored observations and synthetic
   controls explicitly. Separate forecasts, stocks, flows and source-defined
   metrics. Keep overlapping issuer/source windows in the same split.
2. Independently calculate reference tables and claim verdicts from the supplied
   evidence. Declare unique row keys, required columns, numeric tolerances,
   canonical labels and any legitimate source-label aliases. Do not normalize
   different economic categories, periods or measures into the same label.
3. Verify alternative correct SQL, reordered rows and columns, relevant extra
   context and sufficient citation alternatives. Test duplicate keys, omitted
   rows, swapped categories, wrong periods, wrong units, percent scaling, unrelated
   citations and unsupported claim verdicts.
4. Design synthetic controls that change relevant operands while preserving the
   stated definitions and scope. Reject constant answers and forced-zero
   residuals. Preserve independently disclosed discrepancies rather than changing
   observations to make totals reconcile.
5. Check the candidate request, schema and public contract for answer-revealing
   examples or labels. Keep gold, oracle solutions, verifier code, credentials,
   Git history and host sockets outside the candidate image. Require fresh,
   networkless separate verification with bounded SQL workers.

Source rights and synthetic origins follow [the provenance policy](../DATA_SOURCES.md).
Oracle and control checks establish reference behavior, not model performance or
independent human validation.

## Verify the published format

From a checkout with the [documented installation](RUNNING.md), reconstruct the
frozen construction catalog without changing it and check the example JSON:

```sh
.venv/bin/python scripts/build_workflow_pyusd_revision.py --check
./wpb validate examples/block-workpaper-v9/answer.json
```

The versioned builder reconstructs `workflow-v9` from `workflow-v8` in a temporary
directory and compares the output with the frozen package. It is not a generic
new-task generator. Do not edit published packages and regenerate them in place.
A future catalog needs its own reviewed construction and freeze process.

On the installed Linux Docker controller, verify all four submitted files in a
fresh separate verifier and inspect the report:

```sh
./wpb grade --dataset workflow-v9 --task c01 \
  --artifacts examples/block-workpaper-v9 --attempt authoring-reference-1
./wpb report --attempts authoring-reference-1 \
  --output .local/authoring-reference-report.json
```

Use a new attempt ID and output path each time. `validate` checks JSON structure
without executing SQL. `grade` executes SQL only in the separate Docker verifier,
using pristine inputs and controls. A zero process exit alone is not a passing
financial result. Check delivery, numerical tables, claims, evidence, robustness
and isolation in the retained verifier result.

The existing positive and negative construction controls can also be reproduced
on that controller without model calls:

```sh
.venv/bin/python scripts/validate_workflow_quality.py \
  --dataset workflow-v9 --tasks c01 \
  --output .local/authoring-c01-controls.json
```

The [execution guide](RUNNING.md) covers complete oracle sweeps, artifact replay
and credential boundaries. Historical single-JSON/inline-SQL packages remain in
[real-v1](../datasets/real-v1/), with their separate [replay guide](REPLAY.md).
They are not the default construction format.
