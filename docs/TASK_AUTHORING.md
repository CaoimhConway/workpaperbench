# Task authoring

The default suite is `workflow-v15`, the construction track with 30 tasks and
scorer `workflow-1.2.1`. Each task requests three SQL result tables and three
claim verdicts. Candidates receive observations and an output contract, with no
starting SQL. The six development and 24 evaluation cases have separate source
groups. The [methods](WORKFLOW.md) describe the measurement contract and splits.

Author new cases in a distinct future dataset directory. Keep published catalogs,
task IDs and frozen packages unchanged. New source observations, task requests or
grading rules require distinct task and catalog identities before evaluation.
The `workflow-v7` maintenance track is a separate condition with starting queries,
not an interchangeable source of construction results.

## Package and output contract

Use [construction task c01](../datasets/workflow-v15/tasks/c01/) and its
[candidate request](../datasets/workflow-v15/tasks/c01/instruction.md) as a concrete
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
   different economic categories, periods or measures into the same label. Use
   stable entity or period keys, with `keys: []` for a singleton table. Specify
   residual subtraction directions and reported versus reconstructed bases.
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
.venv/bin/python scripts/build_workflow_contract_adjudication.py --check
./wpb validate examples/block-workpaper-v15/answer.json
```

The versioned builder reconstructs `workflow-v15` from `workflow-v14` in a
temporary directory and compares every output byte with the frozen package.
Use the supported Ubuntu 24.04 controller. Earlier database-writing builders
require SQLite 3.45.1 for deterministic database headers. Version 15 copies
those frozen databases rather than rebuilding them. Grading uses the pinned
separate verifier.

Version 15 includes scoped evidence corrections, explicit financial definitions
and a corrected reported baseline for the c10 forecast. Its
[publication bindings](../config/workflow-publication.json) distinguish the
published metadata from the original execution metadata. All task bytes and
scorer code are unchanged by that publication projection.

Do not regenerate a published package in place. Saved outputs from a task with
changed model-visible definitions are diagnostic, not fresh model results.

### Earlier contract revision

The corrected construction catalog is
`workflow-v12-canonical-dc12075916d4`, also using scorer `workflow-1.2.1`.
Select `--dataset workflow-v12` explicitly for this historical condition.
Version 11 commands and frozen comparison configurations retain their original
identity.
Reconstruct the corrected catalog on the same SQLite 3.45.1 controller with:

```sh
.venv/bin/python scripts/build_workflow_grading_contract_revision.py --check
```

Version 12 accepts narrow sufficient claim-evidence alternatives and relevant
Brale observation-date context. Its public contracts distinguish reported from
reconstructed amounts in the Brale, Berkshire, Adobe and Visa tables. The reserve
bridge uses `(June cash + June government debt) - (May cash + May government debt)`.
Independent component and reported-total controls preserve the reconciliation
residual. Original observations, numerical targets, reference SQL, prior controls
and scorer code remain unchanged. Regrading a saved submission after a public
contract change is diagnostic, rather than a fresh result on the revised task.

On the installed Linux Docker controller, verify all four submitted files in a
fresh separate verifier and inspect the report:

```sh
./wpb grade --dataset workflow-v15 --task c01 \
  --artifacts examples/block-workpaper-v15 --attempt authoring-reference-1
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
  --dataset workflow-v15 --tasks c01 \
  --output .local/authoring-c01-controls.json
```

The [execution guide](RUNNING.md) covers complete oracle sweeps, artifact replay
and credential boundaries. Historical single-JSON/inline-SQL packages remain in
[real-v1](../datasets/real-v1/), with their separate [replay guide](REPLAY.md).
They are not the default construction format.
