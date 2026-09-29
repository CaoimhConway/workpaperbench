# WorkpaperBench

WorkpaperBench evaluates whether a research agent can turn financial disclosures
and a starting SQL work product into a usable, source-backed workpaper. An
engineer can inspect a task, run one local model attempt, submit their own bounded
JSON/SQL artifact, and obtain fresh diagnostics from a separate verifier. The
useful target is correct economic measurement with preserved behavior: period
reconstruction, metric repair, reconciliation and an honest boundary around what
the evidence cannot identify.

The current interface uses explicit task and scorer identities. The corrected
`challenge-v2` catalog applies validated **challenge-1.1.3** to every new
submission. The current `workflow-v4` tier requires multiple named result tables
and short structured claim verdicts. Historical releases, original answers,
freezes and correction receipts remain accessible and unchanged.

A clean example is Block's FY2024 consolidated revenue bridge. Its
[filing](https://www.sec.gov/Archives/edgar/data/1512673/000162828025007376/sq-20241231.htm)
reports Bitcoin revenue of USD 10,199,205 thousand versus 9,498,302 thousand, and
total revenue of 24,121,053 thousand versus 21,915,623 thousand. Bitcoin therefore
contributes **31.7808%** of total revenue growth. A retained historical submission
instead returned **-1.0569**, the change in Bitcoin's annual revenue share. Another
returned **0.3178** labeled percent. These are different financial errors, separate
from citation or JSON compliance. The new workflow also requires a gross-profit
bridge, the negative acquired-technology amortization component, reconciliation
residuals and an unresolved verdict for a separate Bitcoin price effect that the
supplied disclosure cannot identify.

| Evidence or gate | Current status |
| --- | --- |
| Corrected published regression catalog | Twelve authored references pass fresh local native verification |
| Historical challenge financial correctness | Inexpensive profile 17/27, reference profile 25/27 |
| Historical corrected strict completion | 8/27 and 18/27 under challenge-1.1.3 |
| New workflow software/data | Six development and 24 evaluation cases pass 180 native quality submissions |
| Local development calibration | Two attempts retained, setup paused, one attempt unstarted |
| Held-out workflow evaluation | Not run, 24 cases verified using references and controls |
| Frontier discrimination | Unmeasured on the workflow tier |
| Human review and external use | Pending |

The historical rows describe the preserved hosted campaign, not the new local
quantization. Completion includes financial outputs, evidence and recomputation,
with delivery reported separately. A low completion rate caused by an evidence
contract is not a financial reasoning failure. Local-model failures do not prove
that leading hosted systems would fail.

The current setup is local-only on an Intel Mac Pro. The measured default
uses Qwen3.5-9B **Q4_K_M**, approximately nine billion parameters, through
llama.cpp b11516 on CPU with a real 65,536-token native window. Thinking mode and
native terminal tools delivered all three SQL files and JSON in a 20m33s setup
smoke. Its original table outputs matched, but claim interpretation and changed-data
checks failed. Earlier configurations and failures remain separately labeled.
Native Harbor/Hermes execution runs in a dedicated Ubuntu 24.04 guest without
host mounts or owner credentials. New external-service spending is USD 0 and no
Actions job is launched during this phase.

Follow the tested setup prerequisites and pinned hashes in
[local execution](docs/LOCAL.md). Then start one server:

```sh
./wpb preflight
./wpb serve
```

In a second terminal, run one task and one attempt:

```sh
./wpb run --task c03 --attempt block-1
```

Use `--dataset workflow-v4 --tasks a01 b01 c01` for a selected development batch.
`--tasks all` selects the current catalog where candidate exposure is permitted.
`--repeat` chooses a bounded repetition count. Every attempt ID is unique, and
existing attempts are rejected. Profiles pin the model, weights, runtime,
template, context, generation settings and resource limits before comparison.
Reports reject mixed configurations.

Grade an engineer's own artifact, replay retained bytes without inference, or
write a new versioned report:

```sh
./wpb grade --task c03 --answer /path/to/answer.json --attempt engineer-1
./wpb replay --task c03 --retained block-1 --attempt block-replay-1
./wpb report --attempts block-1 --output reports/local/block-report.json
```

Workflow grading accepts `--artifacts /path/to/workpaper` with bounded JSON and
read-only SQL files. Replay runs a fresh native separate verifier, preserving
original and normalized hashes. It never overwrites a historical receipt. The
current default demo is `./wpb` and labels authored
references separately from actual submissions. The original console interface
remains available for frozen historical reproduction.

The workflow suite contains six development and 24 evaluation cases, balanced
across updating models, diagnosing metrics, and source-backed attribution.
Expansion passed the three-prototype quality gate and contains 24 evaluation
source-window groups with no development overlap. Eight new cases concern crypto,
payments or stablecoin measurement, seven in evaluation. Previously published inputs are
development/regression material. Authentic observations, source-derived tables,
authored defects, synthetic controls and references have distinct provenance.
Stocks are not flows, signatures are not publication timestamps, and retrieval
today does not establish historical availability.

Declared columns, units, keys, duplicate semantics and tolerances make grading
inspectable. Valid alternative SQL and row order are accepted. Structural
rejection prevents SQL execution, while safe partial claims may remain diagnosed.
Verification uses pristine inputs, network-none and bounded SQL authorization,
time, memory and output. Candidate tools never receive gold or project history.
See [methods](docs/METHODOLOGY.md), [source rights](DATA_SOURCES.md),
[historical results](reports/challenge-v1/reviewed-results.md), the
[blinded review pack](reports/local/human-review-pack.md). No issuer endorsement or private production defect is claimed.
