# WorkpaperBench

Reproducible evaluations for financial research agents

WorkpaperBench tests whether agents can reconcile financial sources, calculate metrics consistently and support their conclusions with frozen financial evidence.

[Quickstart](#quickstart) · [Execution guide](docs/RUNNING.md) · [Methods](docs/WORKFLOW.md) · [Task contract](datasets/workflow-v15/tasks/c01/instruction.md) · [Validation record](reports/workflow-v15/README.md)

## Scope

The benchmark contains 30 source-backed tasks across three financial workflows,
with six development cases and 24 evaluation cases. All tasks are available to
external teams using a compatible model.

| Workflow | Analytical work | Development / evaluation |
| --- | --- | ---: |
| Update a model | Reconstruct quarters, align periods and units, reconcile disclosures | 2 / 8 |
| Audit a metric | Choose denominators, separate stocks from flows, deduplicate exports | 2 / 8 |
| Explain a change | Build signed bridges, reconcile totals, bound causal attribution | 2 / 8 |

The default construction track (`workflow-v15`, scorer `workflow-1.2.1`)
requires agents to write three SQL queries per task, with no starting SQL.
The separate maintenance track (`workflow-v7`) supplies existing queries to
check and repair while preserving correct work. The tracks have distinct
identities and reports. See the [track comparison](docs/WORKFLOW.md#construction-and-maintenance).

Tasks supply source excerpts, normalized observations, definitions and output
contracts. They measure analysis within a fixed dossier, not source extraction,
open-ended search or investment research. Evidence grading checks source
selection, and claim verdicts assess bounded assertions.

Tests include independently calculated reference answers, alternative correct
solutions and targeted counterexamples.

## Evaluation

Each submission contains `answer.json` and three SQL files, with citations and
claim verdicts. A separate verifier runs the SQL against pristine observations
and synthetic controls to check both the original calculations and recomputation
under input changes.

Reports distinguish numerical correctness, claim verdicts, evidence, robustness,
delivery and infrastructure outcomes. Maintenance reports also identify repairs,
preserved results and regressions. Missing or invalid deliveries leave financial
outcomes unassessed. Versioned receipts bind submissions to task, scorer and
configuration hashes.

Retained submissions can be replayed without inference to investigate failures and
check scorer changes.

Model runs use native Harbor. Python graders execute submitted SQL against SQLite
in a separate Docker verifier on Linux, with no network or inference credentials,
read-only access and bounded memory, time and output.

The pytest suite covers graders, reporting and task regressions, with CI in
[GitHub Actions](.github/workflows/ci.yml).

## Quickstart

From the repository root on a Linux controller with uv, Docker Engine and
Docker Compose installed:

```sh
uv tool install --python 3.12 'harbor==0.23.0'
export PYTHONPATH="$PWD"
```

From this checkout, run one `c01` oracle attempt. This uses the authored solution
with no model calls:

```sh
harbor run -p datasets/workflow-v15/tasks -i c01 --agent oracle -k 1 \
  --n-concurrent 1 --max-retries 0 \
  --env workpaperbench.runtime_integrity:VerifiedDockerEnvironment \
  --ek canonical_root="$PWD" \
  --ek expected_manifest=workflow-v15-canonical-400f60b5b3b6 \
  --ek expected_task=workflow-v15-c01 \
  --job-name quickstart-c01-v15-1 --jobs-dir .local/quickstart-v15-1
```

Inspect the job result and its separate-verifier verdict:

```sh
cat .local/quickstart-v15-1/quickstart-c01-v15-1/result.json
cat .local/quickstart-v15-1/quickstart-c01-v15-1/*/verifier/verdict.json
```

Reward should be `1`, `complete` should be `true`, every check should pass and the
job should have no exception. A process exit alone is not a passing financial result.

To evaluate a candidate, set the provider's credential environment variables
and replace the model placeholder. This command requires inference:

```sh
harbor run -p datasets/workflow-v15/tasks -i c01 \
  --agent terminus-2 --model '<provider/model>' --ak max_turns=24 \
  --n-concurrent 1 --max-retries 0 \
  --env workpaperbench.runtime_integrity:VerifiedDockerEnvironment \
  --ek canonical_root="$PWD" \
  --ek expected_manifest=workflow-v15-canonical-400f60b5b3b6 \
  --ek expected_task=workflow-v15-c01 \
  --job-name candidate-c01-v15-1 --jobs-dir .local/candidate-v15-1
```

This is a first-use example, not the frozen comparison condition. Continue with
[full oracle qualification](docs/RUNNING.md#direct-harbor-execution),
[evaluate your own agent](docs/RUNNING.md#evaluate-your-own-agent), and the
[comparison protocol](docs/COMPARISON.md). The versioned comparison and
[pilot protocol](docs/PILOT.md) retain their declared catalog identities. The [v15 validation record](reports/workflow-v15/README.md)
describes software checks and pending independent financial review. These are
not model-performance results.

## Contributing

Contributions can include independently checked references, financial
counterexamples or valid workpapers rejected by the grader. Include the task and
scorer IDs, exact submitted files, expected result and supporting source.

Code is licensed under [MIT](LICENSE). See [source rights and provenance](DATA_SOURCES.md)
for the treatment of public observations, authored materials and synthetic controls.
