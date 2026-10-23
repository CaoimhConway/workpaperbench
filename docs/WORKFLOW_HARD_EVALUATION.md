# Financial reasoning evaluation supplement

`workflow-hard-eval-v1` adds four evaluation tasks to the unchanged 30-task
`workflow-v15` core suite. The first three and subsequent two experimental
cases remain separate development catalogs, `workflow-hard-pilot-v1` and
`workflow-hard-pilot-v2`. These nine additions bring the available core and
supplementary tasks to 39. They do not replace the core suite or its historical
results.

The supplement tests construction of a financial model from disclosed rights,
accounting treatments and cash movements. Its source groups are separate from
those used in development. The financial definitions and candidate inputs were
frozen before their first candidate trials. SQL compatibility revisions carry
separate execution identities. Public financial sources and distributed reference workpapers
preclude a claim that the cases are free from training contamination.

| Task | Analyst question | Additional reasoning |
| --- | --- | --- |
| a01, Albertsons | How much inventory can the credit facility fund? | Resolve different collateral concentration denominators, then connect cash paid for inventory to collateral created by the purchase. |
| b01, BMS | How much did acquisitions cost in accounting and cash terms? | Distinguish business and asset acquisition treatment, cash compensation and noncash consideration, then reconcile cash coverage and comparison bases. |
| c01, Constellation | Did operating cash generation improve across a receivables-financing change? | Separate customer collections, recycled cash and purchaser funding, reconstruct consistent cash-flow categories, and preserve an unexplained retained-interest movement. |
| b02, Reddit | How are liquidation proceeds distributed among owners? | Solve conversion-dependent ownership and contractual priority, then identify owner funding thresholds across a discontinuous mandatory-conversion rule. |

Each [worked reference](../datasets/workflow-hard-eval-v1/references) maps the
financial derivation to the [source snapshots](../datasets/workflow-hard-eval-v1/sources),
explains a distinct valid solution, and records remaining limitations. Relevant
contractual and accounting definitions are supplied. The tasks do not require
web research, missing issuer observations or knowledge of a particular model.
Authored scenarios and synthetic controls are labeled separately from source
facts. Full source documents are not redistributed.

## Run a task

Use the Ubuntu 24.04 Linux controller and pinned Harbor 0.23.0 setup in the
[execution guide](RUNNING.md). Docker Engine and Compose are required. From the
repository root, list the supplement and validate an authored workpaper without
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

Use a fresh attempt ID and output path. The financial reward must be inspected,
not inferred from the process exit. For a native candidate run, obtain the exact
manifest ID from the frozen file and provide your own compatible model endpoint:

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
[custom endpoint configuration](RUNNING.md#direct-harbor-execution) for generation
settings, model metadata and native installed agents. Freeze those settings for
a comparison. The four task IDs are a01, b01, c01 and b02. The supplied native
runs use fresh candidates and isolated verification. An external agent can
instead receive only the instruction and candidate environment files, then
submit the same four-file workpaper for independent grading.

## Scoring and interpretation

The supplement reuses frozen scorer `workflow-1.2.1`, `answer.json` and three SQL
files. SQL tables are evaluated on original and changed-input databases. Claim
verdicts refer only to the original dossier. Equivalent derivations and
sufficient alternative evidence paths pass. Optional explanations are not
semantically verified, and arbitrary choices between equivalent financial
witnesses are not graded.

The supplement versions its SQL worker as `workflow-hard-sql-1.0.1`. It accepts
ordinary `COUNT(*)`, counted CTEs and identifier casing that the earlier worker
incorrectly rejected. Schema objects and table-valued modules remain prohibited.
CTE aliases that use reserved schema or module names remain unsupported. The
financial scorer, SQL resource limits and existing dataset workers are unchanged.
The first correction was frozen before evaluation inference. Version 1.0.1 also
keeps temporary sorting and grouping data in memory, within the same 256 MiB
process limit. Its authored regression was verified before any evaluation
submission or score was inspected. Original executed scores and any subsequent
unchanged-submission reassessment are reported separately.

Candidate resources are unchanged. The qualified Terminus-2 conditions use
3,600 seconds and 24 turns. Native Codex uses the same wall time but has no
supported equivalent turn cap. Agent tools, context management and inference
routes differ, so results compare complete configurations. Installed agents can
expose their inference credential to candidate terminal tools. The separate
verifier has no inference credential, network or Docker socket.

Four tasks support descriptive per-task observations, not a stable general model
ranking. A single outcome moves a four-task score by 25 percentage points. Report
all scheduled attempts, analytical errors, delivery failures, limits and runtime
exceptions. Numerical separation is meaningful only when the underlying errors
measure the intended financial work. Do not infer comparability with scores on
other benchmarks or tune task selection to a desired pass rate.

Independent human financial/source review and actual external-user testing are
separate from software validation and remain pending. The initial development
and final evaluation results are recorded under distinct experiment identities.
The [package verification report](../reports/workflow-hard-eval-v1/README.md)
records the original software gates. The [SQL compatibility correction](../reports/workflow-hard-sql-1.0.1/README.md)
records the revised worker and its verification. Development catalogs retain their
historical contracts. The [second development calibration](../reports/hard-development-20261023/README.md)
documents known worker and evidence-path defects, so its strict completion
counts should not be interpreted as financial reasoning pass rates.
