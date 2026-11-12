# Financial reasoning evaluation supplement

`workflow-hard-eval-v1` adds four evaluation tasks to the unchanged 30-task
`workflow-v15` core suite. Five experimental development tasks stay in separate
catalogs, three in `workflow-hard-pilot-v1` and two in `workflow-hard-pilot-v2`,
for 39 tasks in total. The supplement does not replace the core suite or its
historical results. Report its results separately.

These tasks ask the agent to build a financial model from disclosed rights,
accounting treatments and cash movements. Their source groups are separate from
development. Financial definitions and candidate inputs were frozen before the
first candidate trials. Public sources and distributed reference workpapers
mean the tasks may appear in training data.

| Task | Analyst question | Additional reasoning |
| --- | --- | --- |
| a01, Albertsons | How much inventory can the credit facility fund? | Resolve different collateral concentration denominators, then connect cash paid for inventory to collateral created by the purchase. |
| b01, BMS | How much did acquisitions cost in accounting and cash terms? | Distinguish business and asset acquisition treatment, cash compensation and noncash consideration, then reconcile cash coverage and comparison bases. |
| c01, Constellation | Did operating cash generation improve across a receivables-financing change? | Separate customer collections, recycled cash and purchaser funding, reconstruct consistent cash-flow categories, and preserve an unexplained retained-interest movement. |
| b02, Reddit | How are liquidation proceeds distributed among owners? | Solve conversion-dependent ownership and contractual priority, then identify owner funding thresholds across a discontinuous mandatory-conversion rule. |

Each [worked reference](../datasets/workflow-hard-eval-v1/references) maps the
derivation to the [source snapshots](../datasets/workflow-hard-eval-v1/sources),
explains a distinct valid solution and records remaining limitations. Relevant
contractual and accounting definitions are supplied, so the tasks need no web
research or knowledge of a particular model. Authored scenarios and synthetic
controls are labeled separately from source facts. Full source documents are
not redistributed.

## Run a task

Use the Ubuntu 24.04 Linux controller and pinned Harbor 0.23.0 setup in the
[execution guide](RUNNING.md), with Docker Engine and Compose. From the
repository root, list the supplement and grade an authored workpaper without
inference:

```sh
./wpb list --dataset workflow-hard-eval-v1 --split evaluation
./wpb validate datasets/workflow-hard-eval-v1/tasks/c01/solution/answer.json
mkdir -p .local/hard-reference-c01-workpaper
cp datasets/workflow-hard-eval-v1/tasks/c01/solution/answer.json \
  datasets/workflow-hard-eval-v1/tasks/c01/solution/*.sql \
  .local/hard-reference-c01-workpaper/
./wpb grade --dataset workflow-hard-eval-v1 --task c01 \
  --artifacts .local/hard-reference-c01-workpaper \
  --attempt hard-reference-c01-1
./wpb report --attempts hard-reference-c01-1 \
  --output .local/hard-reference-c01-1.json
```

Use a fresh attempt ID and output path, and read the financial reward rather
than the process exit. For a native candidate run, read the manifest ID from the
frozen file and supply your own compatible model endpoint:

```sh
export PYTHONPATH="$PWD"
manifest_id=$(python3 -c 'import json; print(json.load(open("datasets/workflow-hard-eval-v1/manifest.json"))["manifest_id"])')
harbor run -p datasets/workflow-hard-eval-v1/tasks -i c01 \
  --agent terminus-2 --model '<provider/model>' \
  --ak max_turns=24 --agent-timeout-multiplier 6 \
  --n-concurrent 1 --max-retries 0 \
  --env workpaperbench.runtime_integrity:VerifiedDockerEnvironment \
  --ek canonical_root="$PWD" --ek expected_manifest="$manifest_id" \
  --ek expected_task=workflow-hard-eval-v1-c01 \
  --job-name hard-candidate-c01-1 --jobs-dir .local/hard-candidate-c01-1
```

Set credentials through the provider's supported environment variables. See
[custom endpoint configuration](RUNNING.md#direct-harbor-execution) for
generation settings, model metadata and installed agents, and freeze those
settings for a comparison. The task IDs are a01, b01, c01 and b02. An external
agent can instead receive only the instruction and candidate environment files
and submit the same four-file workpaper for independent grading.

## Scoring and interpretation

The supplement uses frozen scorer `workflow-1.2.1`. SQL tables are evaluated on
original and changed-input databases, and claims refer only to the original
dossier. Equivalent derivations and sufficient alternative evidence paths pass.
Optional explanations are not graded, and neither are arbitrary choices between
equivalent financial witnesses.

The SQL worker is versioned separately as `workflow-hard-sql-1.0.1`. It fixes
the earlier worker's rejection of `COUNT(*)`, counted CTEs and some identifier
casing, and keeps temporary sort data in memory within the same 256 MiB limit.
Both fixes were verified before any evaluation score was inspected. Schema
objects, table-valued modules and CTE aliases with reserved schema or module
names are not supported. See the
[SQL compatibility record](../reports/workflow-hard-sql-1.0.1/README.md).

The qualified Terminus-2 conditions use 3,600 seconds and 24 turns. Native Codex
uses the same wall time but has no equivalent turn cap. Agents, tools, context
management and inference routes differ, so results compare complete
configurations. Installed agents can read their inference credential through
terminal tools. The separate verifier has no inference credential, network or
Docker socket.

Four tasks support per-task observations, not a stable model ranking, since one
outcome moves a score by 25 percentage points. Report every scheduled attempt,
analytical error, delivery failure, limit and runtime exception. Do not compare
these scores with other benchmarks or tune task selection toward a target pass
rate. Independent financial review and external-user testing are pending.

## Records

- [Package verification](../reports/workflow-hard-eval-v1/README.md) - the
  original software gates.
- [Three-configuration calibration](../reports/hard-evaluation-20261023-r2/README.md) -
  all twelve scheduled attempts, original scores and unchanged-submission
  reassessments.
- [Evidence correction](../reports/workflow-hard-evidence-v1/README.md) - two
  sufficient evidence paths accepted after outcome review. Numerical answers,
  controls and candidate-visible files are unchanged.
- [Second development calibration](../reports/hard-development-20261023/README.md) -
  known worker and evidence-path defects, so its completion counts are not
  financial pass rates.
