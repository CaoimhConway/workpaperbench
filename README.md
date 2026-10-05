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

The original baseline of 100 accidentally masked the error. A controlled input change exposed it without a new model call.

This is a real saved submission on a **synthetic task**, not a staged model result. It also omits required SQL aliases and evidence citations, so its original failure cannot be attributed solely to the formula error. [The case study](reports/case-study.md) links the unchanged answer, execution record with its original verdict, and source fixture, and separates those findings.

## What gets evaluated

A plausible answer is not enough. Each task requires the correct values and units, evidence that supports the bounded claims, SQL that recomputes on pristine inputs, and an appropriate conclusion or specific evidence limit.

| Task | Research decision | Source |
|---|---|---|
| [wp01: Quarterly R&D](tasks/wp01/instruction.md) | Derive a quarter from cumulative filing figures | Tesla filing facts |
| [wp02: Event aggregation](tasks/wp02/instruction.md) | Remove duplicate exports without dropping legitimate events | Synthetic ledger |
| [wp03: As-of releases](tasks/wp03/instruction.md) | Use information available at the requested cutoff | Synthetic releases |
| [wp04: Transfer definitions](tasks/wp04/instruction.md) | Compare counts without inventing a time-series conclusion | Synthetic fallback |
| [wp05: Definition migration](tasks/wp05/instruction.md) | Separate reported growth from like-for-like growth | Synthetic migration |
| [wp06: Coverage expansion](tasks/wp06/instruction.md) | Distinguish expanded coverage from growth within matched coverage | Synthetic observations |
| [wp07: Services margins](tasks/wp07/instruction.md) | Reconcile fiscal periods and percentage-point changes | Apple filing facts |
| [wp08: Evidence limits](tasks/wp08/instruction.md) | Report an observable without inventing payment or user labels | Shared synthetic fallback |

Development uses **wp01, wp02 and wp05**. Evaluation uses **wp03, wp04, wp06, wp07 and wp08**, without tuning the intervention on their model outputs.

Two tasks use Tesla and Apple filing facts. Six are synthetic. The bounded public RPC acquisition failed, so two evaluation tasks explicitly share a synthetic replacement. **No result here establishes observed stablecoin-payment adoption.** [Source records and limitations](DATA_SOURCES.md) are part of the deliverable.

## Inspect it locally

Use Python 3.12 for the demo and lightweight tests. No API key, Docker or model download is needed. The demo displays the recorded calculation issue without executing a submitted program.

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

<!-- study-results:start -->

**All scheduled attempts accounted for.** Original verdicts: **48/48**. Corrected verdicts: **47/48**.

| Evaluation arm | Original complete / planned | Corrected complete / planned | Corrected numerical / assessed | Corrected coverage |
|---|---:|---:|---:|---:|
| A | 3 / 15 | 3 / 15 | 13 / 13 | 15 / 15 |
| B | 1 / 15 | 1 / 15 | 13 / 14 | 15 / 15 |

Only evaluation tasks appear here. Development is reported separately. Unfinished or unreviewable trials are not observed zero-score answers. These are coverage-aware counts, not a treatment-effect claim.

[Full results, failures, costs and original records](reports/results.md)

<!-- study-results:end -->

Scalar accuracy was already high. The contract-check skill did not improve verified completion in this recorded comparison. Failures frequently concerned evidence, SQL replay and conclusion contracts. The small, partly synthetic sample supports no causal or significance claim.

Original verdicts and corrected scores are retained side by side. A green Actions job can still contain a scored task failure. Collection and regrading use saved records and no new model calls.

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

Native tests cover reference answers, valid alternatives, wrong periods, constants, joins, abstention, malformed outputs and isolation. New run controls use experiment-scoped identities, pre-setup receipts and ordered A/B pairs. [Methodology](docs/METHODOLOGY.md) explains the supported SQL subset, original-run limitations and correction policy. [The 71-control native report](reports/integration-full-37373492428.json) preserves actual outcomes. [Native compatibility notes](build-notes/NATIVE_COMPATIBILITY.md) document the integration findings.

## Replay a saved submission on Actions

A repository maintainer with Actions write access can dispatch these workflows. Readers cannot dispatch jobs in the owner's repository merely because it is public. Fork this repository, enable Actions and replace `YOUR_LOGIN` below with the fork owner. No inference secret is needed.

Regrade every retained published submission, preserving original verdicts and input hashes:

```bash
gh workflow run ci.yml --repo YOUR_LOGIN/workpaperbench --ref main \
  -f integration=true -f scope=full -f capture=false -f setup=false -f regrade=true
gh run list --repo YOUR_LOGIN/workpaperbench --workflow ci.yml --limit 1
gh run watch RUN_ID --repo YOUR_LOGIN/workpaperbench
gh run download RUN_ID --repo YOUR_LOGIN/workpaperbench --name reviewed-results-COMMIT_SHA-RUN_ID --dir replay-results
```

Inspect `reports/runs/SLOT/regrade.json` inside the result archive for claim-level numerical, evidence, conclusion and replay diagnostics. The archive also contains the original answer and verdict, generated tables, and scorer/input hashes. Treat downloads as untrusted archives and inspect member paths before extraction. A repeated review of identical scorer/input bytes is a verified no-op and preserves the saved result. [Methodology](docs/METHODOLOGY.md) explains raw versus normalized input and the unavailable-answer limitation.

## Native controls and task authoring

Run the key-free native controls in the owner's repository when authorized:

```bash
gh workflow run ci.yml --repo CaoimhConway/workpaperbench --ref main \
  -f integration=true -f scope=full -f capture=false -f setup=false
```

The original freeze is an immutable historical record, not permission to run changed code under its old identity. A new scored experiment needs a new reviewed manifest. Do not retry individual answers for a better score.

The [task-authoring guide](docs/TASK_AUTHORING.md) maps one native package and walks through source review, equivalent answers, changed inputs, native verification and a future freeze. Keep extensions out of the exposed comparison.

**Scope:** a small, partly synthetic regression study over supplied evidence. Not open-web financial research, a leaderboard, a production reliability estimate or an investment recommendation. Repeated attempts and shared source groups are not independent datasets. Provider routing and bootstrap dependencies retain documented variability.

[MIT license](LICENSE) for code. Third-party source material has its own notices in [DATA_SOURCES.md](DATA_SOURCES.md).
