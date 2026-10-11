# WorkpaperBench

Reproducible evaluations for financial research agents

WorkpaperBench tests whether agents can find, reconcile, calculate and justify financial analysis from compact frozen evidence dossiers.

[Quickstart](#quickstart) · [Execution guide](docs/RUNNING.md) · [Methods](docs/WORKFLOW.md) · [Task contract](datasets/workflow-v8/tasks/c01/instruction.md) · [Research prerelease](https://github.com/CaoimhConway/workpaperbench/releases/tag/v0.6.0-rc.1)

## Scope

The benchmark contains **30 source-backed tasks** across three financial workflows,
with six development cases and 24 evaluation cases. All tasks are available to
external teams using a compatible model.

| Workflow | Analytical work | Development / evaluation |
| --- | --- | ---: |
| Update a model | Reconstruct quarters, align periods and units, reconcile disclosures | 2 / 8 |
| Audit a metric | Choose denominators, separate stocks from flows, deduplicate exports | 2 / 8 |
| Explain a change | Build signed bridges, reconcile totals, bound causal attribution | 2 / 8 |

The default **construction track** (`workflow-v8`, scorer `workflow-1.2.0`)
requires agents to write three SQL queries per task, with no starting SQL.
The separate **maintenance track** (`workflow-v7`) supplies existing queries to
check and repair while preserving correct work. The tracks have distinct
identities and reports. See the [track comparison](docs/WORKFLOW.md#construction-and-maintenance).

Tasks supply source excerpts, normalized observations, definitions and output
contracts. They measure analysis within a fixed dossier, not source extraction,
open-ended search or investment research. Evidence grading checks source
selection, and claim verdicts assess bounded assertions.

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

Model runs use native Harbor/Hermes with explicit endpoint configuration and
execution budgets. SQL verification runs separately in an isolated Linux
environment with no network or inference credentials, using read-only access and
bounded memory, time and output.

## Quickstart

Use Python 3.12 to install the package and browse the task catalog:

```sh
git clone https://github.com/CaoimhConway/workpaperbench.git
cd workpaperbench
git checkout v0.6.0-rc.1
python3 -m venv .venv
.venv/bin/pip install -e .
./wpb list --split evaluation
```

To run evaluations, follow the [execution guide](docs/RUNNING.md) to set up a
Linux controller with Docker Engine, Docker Compose and the pinned Harbor/Hermes
runtime. Configure the [model profile](config/external-model.example.json) as
`.local/my-model.json`, setting your endpoint, model identity and budgets.
The endpoint must support Chat Completions and tool calls.

From that controller, run a task, generate its report or evaluate the full split:

```sh
./wpb run --task c09 --profile .local/my-model.json --attempt my-model-c09-1
./wpb report --attempts my-model-c09-1 --output .local/my-model-c09-report.json
./wpb batch --split evaluation --profile .local/my-model.json --attempt my-model-eval-1
```

Use fresh attempt IDs and report paths. Select `--split development` for six
cases or `--split all` for all 30. The execution guide also covers batch reports
and scoring retained workpapers without model inference.

Supply credentials through environment variables. Candidate terminal tools can
read the inference key, so use a dedicated key with appropriate scope and
spending controls. The verifier receives no key.

## Contributing

Contributions can include independently checked references, financial
counterexamples or valid workpapers rejected by the grader. Include the task and
scorer IDs, exact submitted files, expected result and supporting source.

Code is licensed under [MIT](LICENSE). See [source rights and provenance](DATA_SOURCES.md)
for the treatment of public observations, authored materials and synthetic controls.
