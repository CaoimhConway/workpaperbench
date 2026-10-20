# WorkpaperBench

Reproducible evaluations for financial research agents

WorkpaperBench tests whether agents can reconcile financial sources, calculate metrics consistently and support their conclusions with frozen financial evidence.

[Quickstart](#quickstart) · [Execution guide](docs/RUNNING.md) · [Methods](docs/WORKFLOW.md) · [Task contract](datasets/workflow-v9/tasks/c01/instruction.md) · [Research prerelease](https://github.com/CaoimhConway/workpaperbench/releases/tag/v0.6.1-rc.1)

## Scope

The benchmark contains 30 source-backed tasks across three financial workflows,
with six development cases and 24 evaluation cases. All tasks are available to
external teams using a compatible model.

| Workflow | Analytical work | Development / evaluation |
| --- | --- | ---: |
| Update a model | Reconstruct quarters, align periods and units, reconcile disclosures | 2 / 8 |
| Audit a metric | Choose denominators, separate stocks from flows, deduplicate exports | 2 / 8 |
| Explain a change | Build signed bridges, reconcile totals, bound causal attribution | 2 / 8 |

The default construction track (`workflow-v9`, scorer `workflow-1.2.0`)
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

Use a Linux controller with uv, Docker Engine and Docker Compose installed:

```sh
uv tool install --python 3.12 'harbor==0.23.0'
```

First run each of the 30 oracle solutions five times to check your environment.
Oracle runs use the provided reference solutions and make no model calls:

```sh
harbor run \
  --repo CaoimhConway/workpaperbench@v0.6.1-rc.1 \
  -p datasets/workflow-v9/tasks \
  --agent oracle -k 5 \
  --n-concurrent 2 --env docker
```

Every oracle attempt should receive reward `1`. If one fails, include its task,
Harbor version and verifier diagnostics in an [issue](https://github.com/CaoimhConway/workpaperbench/issues/new).

To evaluate a model, set the credentials required by its provider and replace
`<provider/model>` with its Harbor model name:

```sh
harbor run \
  --repo CaoimhConway/workpaperbench@v0.6.1-rc.1 \
  -p datasets/workflow-v9/tasks \
  --agent terminus-2 --model '<provider/model>' \
  --ak max_turns=24 \
  --n-concurrent 2 --env docker
```

This runs all 30 tasks. Use `-i c01` for one development task and adjust concurrency
to your resources. Read the rewards and exceptions in the job result, plus each
trial's `verifier/verdict.json` for financial diagnostics.

The [execution guide](docs/RUNNING.md) covers split filters, custom endpoints,
agent-specific setup and credential boundaries. It also describes the Harbor/Hermes
`wpb` commands for detailed reports and replay without model calls.
The [validation record](reports/workflow-v9/direct-harbor-validation.json) covers
the oracle runs and scripted agent checks. These checks do not measure model performance.

## Contributing

Contributions can include independently checked references, financial
counterexamples or valid workpapers rejected by the grader. Include the task and
scorer IDs, exact submitted files, expected result and supporting source.

Code is licensed under [MIT](LICENSE). See [source rights and provenance](DATA_SOURCES.md)
for the treatment of public observations, authored materials and synthetic controls.
