# WorkpaperBench

### Reproducible evaluations for financial research agents

WorkpaperBench tests whether agents can find, reconcile, calculate and justify financial analysis from compact frozen evidence dossiers. Verified Research Completion requires every requested financial answer, adequate source support and successful changed-input recomputation. Delivery is reported separately. This small offline benchmark has two layers: **Research Challenge** and the preserved **Core Regression** suites.

A [saved Microsoft evaluation workpaper](reports/challenge-v1/workpapers/challenge-v1-evaluation-d9a2fe13f6f2/final-a03-inexpensive-1.md) labels December-quarter revenue of USD 69,632 million and operating income of USD 31,653 million as Q1. Subtracting those amounts from the six-month totals instead gives Q1 revenue of USD 65,585 million and operating income of USD 30,552 million. The saved calculation swaps the quarters and reverses the operating-margin change, reporting +112.6274 instead of -112.6274 basis points. The [reference-model contrast](reports/challenge-v1/workpapers/challenge-v1-evaluation-d9a2fe13f6f2/final-a03-reference-1.md) derives Q1 correctly and passes. Both correctly assess the Azure guidance gap. [Frozen dossier](datasets/challenge-v1/tasks/a03/environment/sources.md) · [Source-first review and excerpt caveat](reports/challenge-v1/showcase-review.json).

Block provides a second substantive failure without that excerpt caveat: the inexpensive model substitutes a change in annual revenue shares for contribution to revenue growth. The reference model's second attempt reports decimal ratios as percentages, making both percentage answers 100 times too small. Its first attempt passes. [Saved Block reference error](reports/runs/challenge-v1-evaluation-d9a2fe13f6f2/final-c03-reference-2/answer.json) · [Source-first diagnosis](reports/challenge-v1/attribution-assessment.json).

The initial pilot is complete. Nine separate evaluation cases passed source review and the hosted software gate. Their 54 full-dossier slots were frozen before exposure as `challenge-v1-evaluation-d9a2fe13f6f2`. [Actions 37568399652](https://github.com/CaoimhConway/workpaperbench/actions/runs/37568399652) is running. The table shows 38 authenticated evaluation answers so far, with all 27 scheduled slots per model retained in completion denominators. Final coverage and all-answer fresh replay remain pending.

| Stage / model | Financial / assessed | Evidence / assessed | Robustness / assessed | Verified / scheduled | Delivery / assessed | Strict / scheduled | Verdict coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| Pilot / Qwen 3.6 35B A3B | 5 / 9 | 4 / 9 | 3 / 9 | 1 / 9 | 9 / 9 | 1 / 9 | 9 / 9 |
| Pilot / Gemini 3.1 Pro Preview | 2 / 9 | 7 / 9 | 6 / 9 | 2 / 9 | 9 / 9 | 2 / 9 | 9 / 9 |
| Evaluation in progress / Qwen 3.6 35B A3B | 12 / 19 | 3 / 19 | 13 / 19 | 2 / 27 | 19 / 19 | 2 / 27 | 19 / 27 |
| Evaluation in progress / Gemini 3.1 Pro Preview | 18 / 19 | 14 / 19 | 18 / 19 | 13 / 27 | 19 / 19 | 13 / 27 | 19 / 27 |

Original evaluation scorer is `challenge-1.1.0`. A [separate versioned evidence correction](datasets/challenge-v1/scoring-review.json) permits an additional relevant NVIDIA income-statement source alongside a complete gross-profit bridge, Ripple's explicit May component schedule as an alternative May citation, Coinbase's direct derivatives/spot scope evidence and Visa's aggregate inputs with lagged timing for its pricing identification limit. The separate review uses `challenge-1.1.3`. It preserves all original verdicts and will be applied consistently to every available evaluation answer. The preserved 1.1.1 and 1.1.2 engineering gates passed. Final 1.1.3 hosted gate [37576954332](https://github.com/CaoimhConway/workpaperbench/actions/runs/37576954332) passed all 29 controls and the engineer-submission path. Consistent corrected scoring and full coverage remain pending. [Source-first evidence diagnosis](reports/challenge-v1/evidence-assessment.json) separates missing support and shared-citation placement from financial or calculation failures. [Growth/attribution diagnosis](reports/challenge-v1/attribution-assessment.json) also separates Block's metric substitution and unsupported fee/pricing conclusions from citation failures. A public-contract ambiguity in shared-context placement is also corrected: related shared references no longer invalidate properly cited claims. The low evidence or completion rates alone do not establish research difficulty.

These original pilot rates include identified unit, evidence and question-contract defects. They do not support model ranking or broad difficulty claims. The [complete pilot assessment](reports/challenge-v1/pilot-assessment.json) separates those defects from three substantive inexpensive-model recomputation failures. Original verdicts stay unchanged. New evaluation contracts remove the incidental traps before exposure. No assisted or repeat pilot runs are scheduled.

The twelve source-backed cases span guidance and adjusted-performance reconciliation, reserve/supply reconstruction, and growth/attribution analysis. Three cases are development and nine are evaluation, with nine independent evaluation issuer/source-window groups and no group crossing the challenge split. Five evaluation cases and one development case concern crypto or stablecoins. Sources include SEC/issuer financial disclosures and reserve reports. Synthetic controls and repeated attempts are not additional observed cases. [Source inventory and rights](DATA_SOURCES.md) · [Measurement and reproduction contract](docs/CHALLENGE.md) · [Challenge records](reports/challenge-v1/results.md).

## Core Regression

**Can an agent calculate the right number - and support the conclusion?**

WorkpaperBench is a small offline evaluation tool for engineers testing financial research agents. Eight native Harbor tasks require a JSON workpaper with numerical answers, source evidence, reproducible SQL and a bounded conclusion. The active `real-v1` suite uses six source-backed tasks and two controlled synthetic diagnostics. It evaluates work over supplied evidence, with separate numerical, conclusion, evidence and replay diagnostics. It is not an open-web research benchmark or a production reliability estimate.

## A source-backed workpaper

**Saved model workpaper [final-wp04-A-1](reports/runs/real-v1-76d0ba6152ff/final-wp04-A-1/answer.json), with [successful native verification](reports/runs/real-v1-76d0ba6152ff/final-wp04-A-1/verdict.json).** Circle's January 2025 reserve report defines circulating USDC as supply on approved blockchains minus tokens allowed but not issued and access-denied tokens. The captured source facts and the workpaper's derived quantities at **January 31, 2025, 23:59 UTC** are:

| Observation | Amount | Unit |
|---|---:|---|
| Total supply on approved blockchains | 54,604,305,445 | USDC |
| Allowed but not issued | 1,291,092,148 | USDC |
| Access denied | 94,273,569 | USDC |
| Derived circulating quantity | **53,218,939,728** | USDC |
| Fair value of reserve assets | **53,283,800,358** | USD |
| Reserves above circulating quantity valued at the issuer's USD 1 redemption convention | **64,860,630** | USD |

The saved workpaper also calculates **16.326677% circulating-quantity growth from January 6 to January 31**. That change in a stock is not transfer volume. The reserve headroom supports a narrow reserve-coverage observation at the report date. It does not establish a market price, payment volume or the number of people using USDC. The report is signed February 27, 2025. Its historical web publication time is unknown. Retrieval now does not make the report point-in-time evidence for January 31.

```sql
SELECT ((reserves_usd - circulation) / 1000000.0) AS value FROM reserve_snapshots WHERE report_date = '2025-01-31'
```

This is the saved workpaper's SQL for reserve headroom in millions of USD. [Task and evidence](datasets/real-v1/tasks/wp04/instruction.md) · [Original issuer report](https://6778953.fs1.hubspotusercontent-na1.net/hubfs/6778953/USDCAttestationReports/2025/2025-USDC_Examination-Report-January-25.pdf) · [Source records and terms](DATA_SOURCES.md).

## Measured results

<!-- versioned-results:start -->

| Dataset / scorer | Model | Arm | Strict / scheduled | Numbers / assessed | Conclusion verdict / assessed | Evidence / assessed | Replay / assessed | Verdict / scheduled | Retained / scheduled |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Historical v1 / 1.2.0 | `qwen/qwen3.6-35b-a3b` | A | 3 / 15 | 13 / 13 | 11 / 11 | 7 / 13 | 7 / 13 | 15 / 15 | 15 / 15 |
| Historical v1 / 1.2.0 | `qwen/qwen3.6-35b-a3b` | B | 1 / 15 | 13 / 14 | 10 / 10 | 7 / 13 | 10 / 13 | 15 / 15 | 15 / 15 |
| real-v1 / 1.2.0 | `qwen/qwen3.6-35b-a3b` | A | 4 / 15 | 15 / 15 | 10 / 11 | 8 / 14 | 10 / 14 | 15 / 15 | 15 / 15 |
| real-v1 / 1.2.0 | `qwen/qwen3.6-35b-a3b` | B | 4 / 15 | 14 / 14 | 11 / 12 | 10 / 14 | 8 / 14 | 14 / 15 | 14 / 15 |

Evaluation only. Development is separate. Historical skill: no improvement. Real-v1: The new campaign has incomplete verdict coverage. Strict completion counts retain the scheduled denominator and cannot establish an intervention benefit.

[New study](reports/real-v1/results.md) · [Historical study and original negative results](reports/results.md). Missing evidence is distinct from an incorrect conclusion. Assessments and retained outputs may have different coverage.

<!-- versioned-results:end -->

The new campaign retained **47 answers and verdicts across 48 scheduled slots**. Apple B1 failed a GitHub API history check before provider access or native trial execution, with no retry. Its exact setup receipt, artifact hashes and the original importer classification remain in the [failure evidence](reports/real-v1/failure-receipts/final-wp07-B-1.json) and [reconciliation assessment](reports/real-v1/final-reconciliation.json). The importer rejected that setup-only record's missing dataset-manifest field, while authenticating and retaining A1 from the same artifact. No model verdict was fabricated for B1.

All 29 retained evaluation workpapers passed the numerical diagnostic, a ceiling on these fixed supplied calculations. That diagnostic does not certify unavailable quantities or broader conclusions. For example, [wp08 A2](reports/runs/real-v1-76d0ba6152ff/final-wp08-A-2/answer.json) incorrectly treats observed Bitcoin outputs as business payments. Conversely, [wp04 B2](reports/runs/real-v1-76d0ba6152ff/final-wp04-B-2/verdict.json) has a correct conclusion verdict and reason but lacks required conclusion evidence. Both arms completed 4/15 scheduled evaluation workpapers. The missing B verdict prevents a fully covered intervention comparison.

Strict completion requires the full declared workpaper contract. A correct conclusion missing a citation is a contract failure, separately diagnosed from an incorrect conclusion verdict. The original 48-trial study remains accessible with its negative intervention result and corrections. Its scores do not evaluate `real-v1`.

## Task inventory

| Task identity | Decision | Provenance | Source group / split |
|---|---|---|---|
| real-v1-wp01 | Quarterly R&D from cumulative filing columns | Source-derived Tesla facts, previously exposed regression | Tesla 2024 Q2 / development |
| real-v1-wp02 | Event identity versus equal amounts and duplicate exports | Synthetic diagnostic with a new control | Authored ledger / development |
| real-v1-wp03 | Sample transaction fees versus coinbase compensation | Source-derived Bitcoin observations | Fixed Bitcoin block samples / evaluation |
| real-v1-wp04 | Circulating stock, change and reserve coverage | Source-derived Circle reserve facts | Circle January 2025 / evaluation |
| real-v1-wp05 | Compare periods under a common metric definition | Synthetic migration, previously exposed regression | Authored migration / development |
| real-v1-wp06 | Compare fee rates on declared transaction coverage | Source-derived Bitcoin observations | Fixed Bitcoin block samples / evaluation |
| real-v1-wp07 | Fiscal-quarter Services margin and percentage-point change | Source-derived Apple facts, previously exposed regression | Apple FY2024 Q2 / evaluation |
| real-v1-wp08 | Output amounts and a bounded evidence limit | Source-derived Bitcoin observations | Fixed Bitcoin block samples / evaluation |

There are **six source-backed base tasks, including four substantive crypto tasks, and two synthetic base tasks**. Three crypto tasks share the same Bitcoin sample bundle. Six tasks do not represent six independent datasets. Deterministic normalization preserves source numerical observations. Every task also has a separately labeled synthetic changed-input replay control. Real-task controls deliberately perturb captured amounts. Diagnostic controls remain fully synthetic. These controls are not observed economic data.

The event diagnostic tests whether export copies are deduplicated without dropping distinct equal-amount events. The migration diagnostic isolates metric comparability under explicit authored definitions. Neither is marketed as observed activity.

Artemis was skipped because no project data credential was available. DefiLlama's free endpoint was inspected but its redistribution terms did not permit this public bundle. The bounded Ethereum log paths failed. The active suite uses SEC accession-specific filing extracts, Circle's issuer report and Bitcoin observations delivered by Blockstream's documented Esplora API. [Source review and exact scope](DATA_SOURCES.md) explain the substitution.

## Run the key-free local demo

Use Python 3.11 or 3.12. Hosted validation uses Python 3.12. No Docker, model or data key is needed. The demo reads a saved source-backed workpaper and displays its calculation without executing submitted SQL.

```bash
git clone https://github.com/CaoimhConway/workpaperbench.git
cd workpaperbench
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/workpaperbench demo
.venv/bin/python scripts/build_real_tasks.py --check
.venv/bin/python -m pytest -q
.venv/bin/workpaperbench report
```

Offline reconstruction checks all frozen input hashes, rebuilds the tables from original captures and compares their schemas and complete typed rows. It retains the hash-verified frozen SQLite bytes after that comparison because physical page layout can differ between SQLite builds. Other package bytes rebuild exactly. No network request is made. Refreshing source data requires a new snapshot identity.

## Fresh replay and your own workpaper

A maintainer with Actions write permission can replay a selected retained submission from scratch, without inference or data credentials. A public reader must fork the repository and enable Actions. Replace `YOUR_LOGIN` with the authorized owner:

```bash
gh workflow run ci.yml --repo YOUR_LOGIN/workpaperbench --ref main \
  -f integration=false -f fresh_replay=true -f dataset=real-v1 \
  -f replay_slot=all
gh run watch RUN_ID --repo YOUR_LOGIN/workpaperbench --exit-status
gh run download RUN_ID --repo YOUR_LOGIN/workpaperbench \
  --name reviewed-results-COMMIT_SHA-RUN_ID --dir replay-results
```

Use `replay_slot=final-wp04-A-1` for one new retained answer. Use `dataset=historical` with `replay_slot=final-wp03-A-1` for the tested historical example. Fresh receipts identify executed native verification, run identity and input/task/scorer hashes, compare earlier diagnostics and preserve them. `regrade=true` is the separate cached historical convenience.

An engineer can commit a bounded `submissions/answer.json` to their fork, following the task's schema, then dispatch the same workflow with `dataset=real-v1`, `answer_path=submissions/answer.json` and `task=wp02`. The supplied [authored reference submission](submissions/reference-wp02.json) demonstrates this path. The submitted SQL executes only in the separate verifier on Actions. [Replay contract and commands](docs/REPLAY.md) · [Task-authoring guide](docs/TASK_AUTHORING.md).

Validation includes 234 lightweight tests, 111 hosted native controls and [fresh verification of all 47 retained answers](https://github.com/CaoimhConway/workpaperbench/actions/runs/37465514129). Every fresh verdict/check comparison matched its retained result. Selected historical replay and the engineer-answer path were also exercised. [Immutable receipts and provenance](reports/real-v1/native-validation.json) retain the run identities, hashes and screening limits.

## Methodology and limits

A and B receive full common instructions. B differs only by the preserved 230-word contract-check skill. The model is `qwen/qwen3.6-35b-a3b` through OpenRouter default routing and the execution framework is Hermes. Development uses wp01/wp02/wp05. Evaluation uses the other five tasks. No shared source bundle crosses that split. Reused questions are exposed regression cases.

The native verifier has no network, inference key or Docker socket. Candidate terminal tools can read their dedicated capped inference key. Native egress restrictions retain DNS/ICMP channels. Output screening is bounded and cannot guarantee detection of arbitrary obfuscation. [Methodology and security boundaries](docs/METHODOLOGY.md) preserve these limits.

The earlier saved formula error remains [historical evidence](reports/case-study.md) on a synthetic task. Original tags, frozen inputs, outputs, verdicts and scorer corrections remain accessible. The source-backed upgrade does not relabel them.

[MIT code license](LICENSE) · [Source-specific rights and attribution](DATA_SOURCES.md) · [Historical measured release](https://github.com/CaoimhConway/workpaperbench/releases/tag/v0.2.0).
