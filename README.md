# WorkpaperBench

### Reproducible evaluations for financial research agents

**Can an agent calculate the right number - and support the conclusion?**

Eight compact tasks test financial evidence selection, metric comparability and replayable SQL workpapers. Built on Harbor with a reference evaluation using Hermes Agent.

[Read the case study](reports/case-study.md) · [Inspect results](reports/results.md) · [Methodology](docs/METHODOLOGY.md) · [Data sources](DATA_SOURCES.md)

## A correct answer can conceal the wrong calculation

In a recorded evaluation trial, the agent reported **20% growth** from 100 to 120 token units. The number was correct. Its submitted SQL implemented the wrong formula.

| Same submitted calculation | Original inputs | Changed-input control |
|---|---:|---:|
| P1 → P2 | 100 → 120 | 120 → 150 |
| Submitted expression: `P2 - P1 * 100 / P1` | 20 | **50** |
| Correct growth: `(P2 - P1) * 100 / P1` | 20% | **25%** |

The original denominator accidentally masked the error. A controlled input change exposed it without a new model call.

This is a real saved submission on a **synthetic task**, not a staged model result. It also has missing SQL aliases and citation requirements, so its original failure cannot be attributed solely to the formula error. [The case study](reports/case-study.md) links the unchanged answer, verdict, execution record and source fixture, and separates those findings.

## What gets evaluated

A plausible answer is not enough. Each task requires the correct values and units, evidence that supports the bounded claims, SQL that recomputes on pristine inputs, and an appropriate conclusion or specific evidence limit.

| Task | Research decision | Split |
|---|---|---|
| Quarterly R&D | Derive a quarter from cumulative filing figures | Development |
| Event aggregation | Remove duplicate exports without dropping legitimate events | Development |
| Definition migration | Separate reported growth from like-for-like growth | Development |
| As-of releases | Choose information available at the requested cutoff | Evaluation |
| Transfer definitions | Compare two counts without inventing a time-series conclusion | Evaluation |
| Coverage expansion | Distinguish more coverage from growth within the same coverage | Evaluation |
| Services margins | Reconcile fiscal periods and percentage-point changes | Evaluation |
| Evidence limits | Report an observable statistic without inventing payment or user labels | Evaluation |

Two tasks use Tesla and Apple filing facts. Six are synthetic. The bounded public RPC acquisition failed, so two evaluation tasks explicitly share a synthetic replacement. **No result here establishes observed stablecoin-payment adoption.** [Source records and limitations](DATA_SOURCES.md) are part of the deliverable.

## Inspect it locally

The demo needs no API key, Docker or model download. It displays the recorded calculation issue without executing a submitted program.

```bash
git clone https://github.com/CaoimhConway/workpaperbench.git
cd workpaperbench
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/workpaperbench demo
.venv/bin/python -m pytest -q
```

To regenerate the tables from retained records:

```bash
.venv/bin/workpaperbench report
```

## The study and its current status

The frozen comparison has **48 scheduled trials**: eight tasks, two configurations and three fresh attempts. The main evaluation contains 30 trials. The other 18 final trials and 12 earlier exploratory attempts are reported separately.

**A** receives the full task instructions and structural checker. **B** receives those same inputs plus one 230-word contract-check skill selected after development observations. The underlying model is `qwen/qwen3.6-35b-a3b` through OpenRouter. Hermes Agent is the execution framework, not a claim that a Nous model was evaluated.

**The empirical comparison is not yet a finished release.** [Results](reports/results.md) state the latest imported record count, actual workflow states, original verdicts and any reviewed verdicts. Missing records are not zero-score answers, and a green Actions job can still contain a scored task failure. There is no claimed treatment improvement before the completed evidence supports it.

The original experiment remains pinned to its [execution snapshot](https://github.com/CaoimhConway/workpaperbench/tree/b4e256dc8976223a8a3fdad157a6b212f49bb8e1) and [run](https://github.com/CaoimhConway/workpaperbench/actions/runs/37280454673). Scorer corrections are versioned separately. They do not rewrite its inputs, original verdicts or live jobs.

## How verification works

```text
Frozen tables + source context
              ↓
     Hermes → answer.json
              ↓
Separate verifier → original + changed-input SQL replay
              ↓
Original verdict + independent diagnostics + retained evidence
```

The reviewed grader accepts valid alternative SQL, distinguishes a wrong conclusion from a missing citation, and can inspect a uniquely identifiable requested answer even when extra output makes strict format fail. It never repairs an answer to award a pass.

The replay worker is read-only, function-restricted, resource-bounded and isolated from inference credentials. All Docker, Harbor and live execution belong on GitHub-hosted Ubuntu runners. The local machine only edits, runs lightweight tests and views results.

Native tests cover reference answers, valid alternatives, wrong periods, constants, joins, abstention, malformed outputs and isolation. New run controls use experiment-scoped identities, pre-setup receipts and ordered A/B pairs. [Methodology](docs/METHODOLOGY.md) explains the supported SQL subset, original-run limitations and correction policy. [Native compatibility notes](build-notes/NATIVE_COMPATIBILITY.md) document the integration findings.

## Reproduce and contribute

Run the key-free native controls through Actions:

```bash
gh workflow run ci.yml --repo CaoimhConway/workpaperbench --ref main \
  -f integration=true -f scope=full -f capture=false -f setup=false
```

The original freeze is an immutable historical record, not permission to run changed code under its old identity. A new scored experiment needs a new reviewed manifest. Do not retry individual answers for a better score.

To improve a task, start with its `sources/wpXX.json`, independently check the evidence and reference calculation, and add both a legitimate alternative and a plausible wrong submission to the tests. Keep changes out of an exposed comparison. There is no need to add a dashboard, new model or evaluation framework.

**Scope:** a small, partly synthetic regression study over supplied evidence. Not open-web financial research, a leaderboard, a production reliability estimate or an investment recommendation. Repeated attempts and shared source groups are not independent datasets. Provider routing and bootstrap dependencies retain documented variability.

[MIT license](LICENSE) for code. Third-party source material has its own notices in [DATA_SOURCES.md](DATA_SOURCES.md).
