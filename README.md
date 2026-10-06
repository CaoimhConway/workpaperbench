# WorkpaperBench

### Reproducible evaluations for financial research agents

**Can an agent calculate the right number - and support the conclusion?**

WorkpaperBench is a small offline evaluation tool for engineers testing financial research agents. Eight native Harbor tasks require a JSON workpaper with numerical answers, source evidence, reproducible SQL and a bounded conclusion. The active `real-v1` suite uses six source-backed tasks and two controlled synthetic diagnostics. It evaluates work over supplied evidence, with separate numerical, conclusion, evidence and replay diagnostics. It is not an open-web research benchmark or a production reliability estimate.

## A source-backed workpaper

**Authored reference, not a recorded model submission.** Circle's January 2025 reserve report defines circulating USDC as supply on approved blockchains minus tokens allowed but not issued and access-denied tokens. At **January 31, 2025, 23:59 UTC**:

| Observation | Amount | Unit |
|---|---:|---|
| Total supply on approved blockchains | 54,604,305,445 | USDC |
| Allowed but not issued | 1,291,092,148 | USDC |
| Access denied | 94,273,569 | USDC |
| Derived circulating quantity | **53,218,939,728** | USDC |
| Fair value of reserve assets | **53,283,800,358** | USD |
| Reserves above circulating quantity valued at the issuer's USD 1 redemption convention | **64,860,630** | USD |

That supports a narrow reserve-coverage observation at the report date. It does not establish a market price, payment volume or the number of people using USDC. The report is signed February 27, 2025. Its historical web publication time is unknown. Retrieval now does not make the report point-in-time evidence for January 31.

```sql
SELECT (approved_supply - allowed_unissued - access_denied) / 1000000.0 AS value
FROM reserve_snapshots WHERE report_date = '2025-01-31'
```

This produces circulating quantity in millions of USDC. [Task and evidence](datasets/real-v1/tasks/wp04/instruction.md) · [Original issuer report](https://6778953.fs1.hubspotusercontent-na1.net/hubfs/6778953/USDCAttestationReports/2025/2025-USDC_Examination-Report-January-25.pdf) · [Source records and terms](DATA_SOURCES.md).

## Measured results

<!-- versioned-results:start -->

| Dataset / scorer | Model | Arm | Strict / scheduled | Numbers / assessed | Conclusion verdict / assessed | Evidence / assessed | Replay / assessed | Verdict / scheduled | Retained / scheduled |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Historical v1 / 1.2.0 | `qwen/qwen3.6-35b-a3b` | A | 3 / 15 | 13 / 13 | 11 / 11 | 7 / 13 | 7 / 13 | 15 / 15 | 15 / 15 |
| Historical v1 / 1.2.0 | `qwen/qwen3.6-35b-a3b` | B | 1 / 15 | 13 / 14 | 10 / 10 | 7 / 13 | 10 / 13 | 15 / 15 | 15 / 15 |
| real-v1 / 1.2.0 | `qwen/qwen3.6-35b-a3b` | A | Pending | Pending | Pending | Pending | Pending | 0 / 15 | 0 / 15 |
| real-v1 / 1.2.0 | `qwen/qwen3.6-35b-a3b` | B | Pending | Pending | Pending | Pending | Pending | 0 / 15 | 0 / 15 |

Evaluation only. Development is separate. Historical skill: no improvement. Real-v1: New measured results are pending. The historical intervention outcome does not evaluate this dataset.

[New study](reports/real-v1/results.md) · [Historical study and original negative results](reports/results.md). Missing evidence is distinct from an incorrect conclusion. Assessments and retained outputs may have different coverage.

<!-- versioned-results:end -->

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

Use Python 3.12. No Docker, model or data key is needed. The demo reads a saved source-backed workpaper and displays its calculation without executing submitted SQL.

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
  -f integration=false -f fresh_replay=true -f dataset=historical \
  -f replay_slot=final-wp03-A-1
gh run watch RUN_ID --repo YOUR_LOGIN/workpaperbench --exit-status
gh run download RUN_ID --repo YOUR_LOGIN/workpaperbench \
  --name reviewed-results-COMMIT_SHA-RUN_ID --dir replay-results
```

Use `dataset=real-v1` to replay the new study, or `replay_slot=all` for every retained answer. Fresh receipts identify executed native verification, run identity and input/task/scorer hashes, compare earlier diagnostics and preserve them. `regrade=true` is the separate cached historical convenience.

An engineer can commit a bounded `submissions/answer.json` to their fork, following the task's schema, then dispatch the same workflow with `dataset=real-v1`, `answer_path=submissions/answer.json` and `task=wp02`. The supplied [authored reference submission](submissions/reference-wp02.json) demonstrates this path. The submitted SQL executes only in the separate verifier on Actions. [Replay contract and commands](docs/REPLAY.md) · [Task-authoring guide](docs/TASK_AUTHORING.md).

## Methodology and limits

A and B receive full common instructions. B differs only by the preserved 230-word contract-check skill. The model is `qwen/qwen3.6-35b-a3b` through OpenRouter default routing and the execution framework is Hermes. Development uses wp01/wp02/wp05. Evaluation uses the other five tasks. No shared source bundle crosses that split. Reused questions are exposed regression cases.

The native verifier has no network, inference key or Docker socket. Candidate terminal tools can read their dedicated capped inference key. Native egress restrictions retain DNS/ICMP channels. Output screening is bounded and cannot guarantee detection of arbitrary obfuscation. [Methodology and security boundaries](docs/METHODOLOGY.md) preserve these limits.

The earlier saved formula error remains [historical evidence](reports/case-study.md) on a synthetic task. Original tags, frozen inputs, outputs, verdicts and scorer corrections remain accessible. The source-backed upgrade does not relabel them.

[MIT code license](LICENSE) · [Source-specific rights and attribution](DATA_SOURCES.md) · [Historical measured release](https://github.com/CaoimhConway/workpaperbench/releases/tag/v0.2.0).
