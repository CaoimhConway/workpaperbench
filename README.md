# WorkpaperBench

**Reproducible evaluations for financial research agents.**

*Can an agent calculate the right number - and support the conclusion?*

WorkpaperBench tests the work behind a financial answer: the evidence selected, the metric definition, the executable calculation, and the conclusion. Eight small tasks run through Harbor with Hermes Agent. Answers are checked against frozen source material and replayed on changed inputs, not scored by another language model.

[Read the case study](reports/case-study.md) · [Inspect the tasks](#what-the-tasks-test) · [Run the local demo](#try-it-locally) · [Results and status](#results-and-status)

## Correct answer. Wrong formula.

An actual baseline submission reported **20% growth** from 100 to 120. Its submitted SQL used an expression equivalent to `P2 - P1 * 100 / P1`, rather than `100 * (P2 - P1) / P1`.

| Inputs | Submitted expression | Correct growth |
|---|---:|---:|
| P1 = 100, P2 = 120 | 20 | 20% |
| P1 = 120, P2 = 150 | **50** | **25%** |

The first result looks right because the starting value happens to be 100. The changed-input control exposes the incorrect formula.

**This is a saved model response on a synthetic task, not an invented demonstration.** It also had missing SQL aliases and incomplete evidence references. Those defects contributed to the original failure, so the formula inspection is not presented as its sole grading cause. [The case study](reports/case-study.md) includes the arithmetic reproduction, original run identity, artifact digest, and limits of the finding.

That is the purpose of a workpaper: make a plausible answer inspectable before anyone relies on it.

## What the tasks test

| Task | Research operation | What a final-number check can miss | Source |
|---|---|---|---|
| [wp01](tasks/wp01/instruction.md) | Derive quarterly R&D from cumulative figures | Wrong reporting period or growth denominator | Tesla filing facts |
| [wp02](tasks/wp02/instruction.md) | Aggregate a transfer-event export | Removing genuine events while deduplicating copied records | Synthetic ledger |
| [wp03](tasks/wp03/instruction.md) | Calculate growth as of a publication cutoff | Later revisions, ineligible evidence, unsupported USD valuation | Synthetic releases |
| [wp04](tasks/wp04/instruction.md) | Compare two aggregation definitions | Mistaking a within-window definition difference for growth over time | Synthetic fallback |
| [wp05](tasks/wp05/instruction.md) | Reconcile a metric-definition migration | Comparing totals built with incompatible counting rules | Synthetic migration |
| [wp06](tasks/wp06/instruction.md) | Separate feed expansion from like-for-like growth | Changing coverage and one-to-many join inflation | Synthetic observations |
| [wp07](tasks/wp07/instruction.md) | Derive quarterly Services margins | Cumulative periods, rounding, percent versus percentage points | Apple filing facts |
| [wp08](tasks/wp08/instruction.md) | Assess what transfer logs establish | Treating transfers as identified business payments or unique humans | Shared synthetic fallback |

Development uses **wp01, wp02, wp05**. Evaluation uses **wp03, wp04, wp06, wp07, wp08**, without tuning the intervention on their model outputs. The two fallback tasks share a corpus and are not independent datasets. [Data sources and provenance](DATA_SOURCES.md) distinguish every origin.

The public stablecoin-methodology change motivates the comparability question. The fixture does **not** reconstruct Artemis's proprietary historical filters or establish a defect in its product.

## How verification works

```text
Frozen tables + source excerpts
              |
       Hermes Agent
              |
         answer.json
   values / evidence / SQL / verdict
              |
     Separate trusted verifier
       |                 |
 original inputs    changed-input control
              |
  task verdict + diagnostic checks
```

An answered numerical claim must have the expected value and units, appropriate evidence, and SQL that reproduces the requested quantity. Unavailable inputs are not treated as zero. A bounded conclusion must be supported by the supplied evidence, and positive controls prevent blanket refusal from succeeding.

Submitted SQL runs against pristine databases in a constrained process. Candidate Python and candidate databases are never executed by the host. The native verifier runs separately without an inference key, host Docker socket, or external network. Both experimental arms receive the same task requirements and structural checker.

A pass is conjunctive: polished output cannot compensate for a wrong result. Diagnostics matter just as much as the headline score: a malformed response, missing citation, wrong formula, and unsupported conclusion are different failures.

## The experiment

| Setting | Frozen configuration |
|---|---|
| Agent | Hermes Agent through Harbor's installed integration |
| Underlying model | `qwen/qwen3.6-35b-a3b` through OpenRouter |
| A | Complete common instructions and output checker |
| B | A plus one 230-word contract-check skill |
| Scheduled work | 8 tasks × 2 arms × 3 fresh attempts = **48 trials** |
| Main evaluation | **30 evaluation trials**, separate from 18 development trials |
| Exploration | 12 recorded development attempts, including failures |
| Execution | Standard GitHub-hosted Ubuntu runners |

The skill targets output-contract and recomputation lapses observed in development. It adds no task answers or privileged evidence. The configuration fixes the model and intervention before evaluation. The default provider route can still vary, so this is not a claim of identical serving conditions or bit-for-bit reproducibility.

Repeated attempts remain separate records. There is no best-of-three score, broad model ranking, or statistical-significance claim. [Runtime pins](config/runtime.json), [the freeze](config/freeze.json), and [the schedule](config/schedule.json) are inspectable.

## Results and status

**Software preview. The first empirical release is not complete.** The frozen campaign is [run 37280454673](https://github.com/CaoimhConway/workpaperbench/actions/runs/37280454673). Checked-in reports are snapshots, not a live view of that run.

At the reviewed source revision, [the report](reports/results.md) contains no final trial records. Its `0 / scheduled` entries must **not** be read as observed zero accuracy. The case above comes from an actual downloaded trial artifact. A green Actions job means execution finished, not necessarily that the task passed.

The review also identified undocumented SQL-function restrictions, incomplete retention of malformed answers, and resume/accounting edge cases. Until the corrections are validated and retained outputs are consistently regraded, the original scores are provisional. Original records, frozen inputs, and corrected verdicts must remain separately identifiable. No treatment-uplift claim is made here.

[Build status](BUILD_STATUS.md) records completed gates and run IDs. The earlier software gate reported 128 lightweight tests and 64 native controls. Those counts are evidence of checks performed, not proof that a grader has no defects.

## Try it locally

Python 3.12 or later is sufficient for the authored demo and lightweight tests. **No API key or local Docker is needed.**

```sh
git clone https://github.com/CaoimhConway/workpaperbench.git
cd workpaperbench
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/workpaperbench demo
.venv/bin/python -m pytest -q
```

The demo prints a source-backed Tesla reference workpaper. It is labeled authored and is separate from model submissions. The [case study](reports/case-study.md#reproduce-the-arithmetic-without-credentials-or-containers) also contains a small, key-free arithmetic reproduction of the observed formula issue.

To regenerate a report from the records already checked out:

```sh
.venv/bin/workpaperbench report
```

Do not execute downloaded candidate programs on your own machine. Full container verification belongs on Actions. For the repository owner, the existing key-free native gate is:

```sh
gh workflow run ci.yml --repo CaoimhConway/workpaperbench --ref main \
  -f integration=true -f scope=full -f capture=false -f setup=false
```

Live trials require a separate capped inference credential. Do not redispatch or use GitHub's rerun controls as a shortcut for a failed score. See [setup](SETUP.md) and [execution notes](build-notes/ACTIONS.md) before any paid run.

## Scope and limitations

This is a compact regression suite over curated local tables and source excerpts. It does not evaluate open-web research, document extraction, valuation judgment, trading returns, or production financial-agent reliability.

Two tasks use public-company filing facts. Six use original synthetic scenarios, including the disclosed fallback after the bounded historical-log acquisition failed. No result from that fallback establishes observed chain activity, payment adoption, or unique-user counts.

Evidence grading checks reviewed identifiers and claim-specific support requirements. It is not a general semantic verifier. Changed-input replay catches particular wrong methods, not every program that could overfit two fixtures. Some evidence-limit questions are directly cued by the supplied scope notes.

The installed agent can read its dedicated capped inference key. Its TCP filtering is not absolute egress isolation, and upstream bootstrap dependencies remain moving parts. The verifier's stronger boundary and the agent's residual limitations are documented separately. [Native compatibility findings](build-notes/NATIVE_COMPATIBILITY.md) explain the small installed-adapter corrections and their execution evidence.

## Extend one task, not the framework

Task definitions live in `sources/wp*.json`. Review the source context and reference calculation, add legitimate alternative solutions and plausible wrong answers, then regenerate the native packages:

```sh
.venv/bin/python scripts/build_tasks.py
.venv/bin/python -m pytest -q
```

Run the separate native gate before a new release. Candidate inputs must not contain gold answers. After evaluation exposure, changed tasks, instructions, or interventions require a new experiment identity. Grader-only corrections should preserve original verdicts and apply consistently across both arms.

[MIT license](LICENSE) covers the code. [DATA_SOURCES.md](DATA_SOURCES.md) records third-party source notices and the origins of factual extracts and synthetic fixtures.
