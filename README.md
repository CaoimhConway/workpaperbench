# WorkpaperBench

[![CI](https://github.com/CaoimhConway/workpaperbench/actions/workflows/ci.yml/badge.svg)](https://github.com/CaoimhConway/workpaperbench/actions/workflows/ci.yml)

Reproducible evaluations for financial research agents

WorkpaperBench tests whether a financial agent's analysis can be trusted, not
just whether its final numbers look right. Each task supplies a small dossier
from public filings or reserve reports. The agent delivers a workpaper: three
SQL queries that build the requested tables and verdicts on three claims, with
source citations for every output. A separate verifier reruns the submitted SQL
on the original data and on changed copies of it, so a calculation that is
right only by coincidence fails.

[Results](#results) · [Quickstart](#quickstart) · [How scoring works](#how-scoring-works) · [Methods](docs/WORKFLOW.md) · [Execution guide](docs/RUNNING.md)

## What it catches

In one recorded trial an agent reported the correct 20% growth, but its SQL
computed `P2 - P1 * 100 / P1` instead of `(P2 - P1) * 100 / P1`. With P1 = 100
the two formulas agree. With P1 = 120 and P2 = 150 the submitted formula gives
50% instead of 25%. Checking only the final number would have accepted it. The
[case study](reports/case-study.md) shows the retained submission and its
original verdict.

Every submission is scored on five separate dimensions:

| Dimension | Question |
| --- | --- |
| Numerical | Do the SQL results match the reference rows within declared tolerances? |
| Robustness | Does the same SQL stay correct when controlled inputs change? |
| Claims | Is each assertion correctly judged supported, contradicted or unresolved by the dossier? |
| Evidence | Does each table and claim cite sources sufficient to support it? |
| Delivery | Were exactly the requested files delivered, within size and safety limits? |

A workpaper is complete only when all five pass.

## Results

### Financial reasoning supplement

Four evaluation tasks, one fresh attempt per task and configuration, October
2026. See the [full report](reports/hard-evaluation-20261023-r2/README.md).

| Task | GLM-5.3 | DeepSeek v4.1 Flash | GPT-6.1 Sol |
| --- | --- | --- | --- |
| a01 Albertsons - borrowing capacity | No `answer.json` | Pass | Pass |
| b01 BMS - acquisition accounting | Pass | Correct numbers, incomplete citations | Pass |
| b02 Reddit - liquidation rights | No `answer.json` | No `answer.json` | Pass |
| c01 Constellation - receivables financing | Pass\* | Timed out | Numerical error |
| **Complete workpapers** | **2/4** | **1/4** | **3/4** |

\*Passes after a documented correction that accepts a sufficient citation path.
The correction followed outcome review. Original scores were 1/4, 1/4 and 3/4.

- Seven of the eight delivered workpapers passed every numerical and
  changed-input check. Most failures came from agents that did not finish or
  did not cite enough sources.
- Sol's c01 error treated a loss on receivables sales as an extra reduction of
  the retained interest. It reported 535 explained and +15 unallocated against
  the correct 578 and -28, and the error persisted on all eight controls.
- The GLM and DeepSeek attempts cost USD 1.39 through OpenRouter. Sol ran on a
  subscription, and its charge was not measured.

Configurations differ in agent, tools and provider route. With four tasks, one
outcome moves a score by 25 percentage points.

### Earlier results

- **Development calibration.** On three harder development tasks, GLM-5.3 and
  GPT-6.1 Sol both completed 3/3, so those tasks do not separate the two
  ([report](reports/hard-calibration-20261023/README.md)).
- **Research Challenge, retired catalog.** Gemini 3.1 Pro Preview completed
  17/27 evaluation workpapers versus 2/27 for Qwen3.6-35B-A3B as originally
  scored, and 18/27 versus 8/27 after a documented evidence-scoring review
  ([results](reports/challenge-v1/reviewed-results.md)).

Model results on the current 30-task core catalog are not yet published.

## The benchmark

The core suite has 30 tasks, six for development and 24 for evaluation. Sources
include filings from Block, Coinbase, Circle, PayPal, Robinhood, Visa, Nvidia
and Apple, and the PYUSD and Brale reserve reports.

| Workflow | Analytical work | Development / evaluation |
| --- | --- | ---: |
| Update a model | Reconstruct quarters, align periods and units, reconcile disclosures | 2 / 8 |
| Audit a metric | Choose denominators, separate stocks from flows, deduplicate exports | 2 / 8 |
| Explain a change | Build signed bridges, reconcile totals, bound causal attribution | 2 / 8 |

The [financial reasoning supplement](docs/WORKFLOW_HARD_EVALUATION.md) adds four
evaluation tasks on borrowing capacity, acquisition accounting, receivables
financing and liquidation rights. Report its results separately from the core
suite.

Tasks supply source excerpts, normalized observations, definitions and an
output contract. They test analysis within a fixed dossier, not source
extraction or open-ended research. The default construction track
(`workflow-v15`, scorer `workflow-1.2.1`) supplies no starting SQL. A separate
maintenance track (`workflow-v7`) supplies existing queries to check and repair.
Read an example [task instruction](datasets/workflow-v15/tasks/c01/instruction.md)
and its [reference workpaper](examples/block-workpaper-v15).

## Quickstart

See the formula case and preserved submissions without Docker or a model:

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m workpaperbench.cli demo
```

Scoring runs submitted SQL only inside an isolated Linux verifier. From the
repository root on a Linux controller with uv, Docker Engine and Docker Compose
installed:

```sh
uv tool install --python 3.12 'harbor==0.23.0'
export PYTHONPATH="$PWD"
```

Run one `c01` oracle attempt. This uses the authored solution with no model
calls:

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

Reward should be `1`, `complete` should be `true`, every check should pass and
the job should have no exception. A process exit alone is not a passing result.

To evaluate your own model, set the provider's credential environment variables
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

This is a first run, not the frozen comparison condition. Continue with
[full oracle qualification](docs/RUNNING.md#direct-harbor-execution),
[evaluating your own agent](docs/RUNNING.md#evaluate-your-own-agent) and the
[comparison protocol](docs/COMPARISON.md).

## How scoring works

See [scorer files and catalog bindings](docs/WORKFLOW.md#scorer-files) for the
current and historical implementations.

The verifier runs in a separate Docker container with no network, inference
credential or Docker socket. Submitted SQL runs read-only against SQLite, with
an allowlist of SQL operations and limits on memory, CPU time and output. Each
query is replayed on the original observations and on three to six synthetic
controls that exercise period filters, monetary scaling, component changes and
disagreements between reported totals and their components. Different SQL is
accepted when its results agree.

Versioned receipts bind every submission to its task, scorer and configuration
hashes. Retained submissions can be [replayed without inference](docs/REPLAY.md)
to check scorer changes. Original verdicts are never overwritten. Corrections
are published as separate versions. The [v15 validation record](reports/workflow-v15/README.md)
lists the software checks for the current catalog.

Known limits:

- Tasks use public sources, so training contamination is possible.
- Results compare complete agent configurations, not models in isolation.
- Native installed agents can read their inference credential through terminal tools.
- Independent financial review of the tasks and external replication are pending.

See [methods and limits](docs/WORKFLOW.md) for details.

## Contributing

Contributions can include independently checked references, financial
counterexamples or valid workpapers rejected by the grader. Include the task and
scorer IDs, exact submitted files, expected result and supporting source.

Code is licensed under [MIT](LICENSE). See [source rights and provenance](DATA_SOURCES.md)
for the treatment of public observations, authored materials and synthetic controls.
