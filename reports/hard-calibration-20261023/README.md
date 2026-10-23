# Harder-tier development calibration - 23 October 2026

GLM-5.3 through Terminus-2 and GPT-6.1 Sol through native Codex each completed **3/3 workpapers (100%)**. Every scored dimension passed on all three tasks. These six observations are a development calibration of two model-and-agent configurations. They are not held-out results, identical-agent testing, a general model ranking or evidence that a target difficulty has been achieved.

The [frozen six-slot manifest](../../config/hard-calibration-20261023/manifest.json), [GLM condition](../../config/hard-calibration-20261023/glm.json), [Sol condition](../../config/hard-calibration-20261023/sol.json), [final ledger](ledger.json), [results](results.json) and [verification summary](verification.json) provide the identities and evidence. The original proposed calibration recipe remains unchanged.

## Results and financial review

| Development task | GLM complete | Sol complete | Control databases per submission | Review of the submitted calculations | Recommendation |
| --- | --- | --- | ---: | --- | --- |
| a01 - Ahold Delhaize comparability | 1/1 | 1/1 | 6 | Both reinstate signed Q4 calendar/divestment adjustments, remove the disclosed extra week, let that week cancel from pre-Q4, and calculate an independent segment/group residual. | Retain for period and perimeter reconstruction coverage. This observation supplies no evidence of discrimination between these conditions. |
| b01 - Microsoft cash and assets | 1/1 | 1/1 | 7 | Both distinguish cash principal from noncash recognition, use the positive payable change, avoid double-counting lease amortization and leave residuals unallocated. | Retain for cash-versus-recognition coverage, subject to the existing rounded-input and depreciation-scope limitations. |
| c01 - Apple identification and bounds | 1/1 | 1/1 | 5 | GLM enumerates feasible vertices. Sol fills regional capacities in objective-coefficient order. Both optimize revenue and gross profit separately and recompute under slope reversal and capacity changes. | Retain for optimization coverage. Supplement a future design with structured feasibility/optimality evidence if demonstrating sharpness itself is intended to be graded. |
| Total | **3/3** | **3/3** | 18 distinct package controls | All original and control comparisons pass. | Retain these as development correctness cases. Supplement before making a harder-tier or discriminative-difficulty claim. |

Across both conditions, all 18 original table comparisons, 108 control-table comparisons and 18 original-dossier claim verdicts pass. Evidence, robustness and strict four-file delivery also pass in every attempt. Each submission contains `answer.json` and its three named SQL files. The authoritative scorer is unchanged `workflow-1.2.1`.

The [workpapers](workpapers) and [per-attempt receipts](receipts) retain exact artifact hashes, table-by-table original/control outcomes, claim/evidence outcomes and verifier diagnostics. No candidate SQL was executed on the macOS host. The separate native verifiers recomputed it against pristine original and control databases.

Review against the [worked references](../../datasets/workflow-hard-pilot-v1/references) occurred after all six submissions were final. Ahold's matched annual change is EUR 2,195 million, with a EUR 745 million extra-week adjustment and a -10,042 million presentation bridge. Both queries preserve an independently changed group total rather than hard-coding a zero residual. Microsoft's capital cash outlay is USD 66,834 million, purchase proxy USD 67,151 million, total net-PPE residual USD 3,713 million and finance-lease net residual USD 1,050 million. Both submissions preserve the cash/noncash and nested depreciation distinctions.

Apple's revenue-loss interval is USD 33,001.91-42,789.17 million and gross-profit-loss interval approximately USD 14,822.717152-16,615.153124 million. The two submissions use materially different valid optimization routes. Their SQL supports both objectives under changed inputs rather than assuming the revenue-minimizing allocation also minimizes gross-profit loss. Arbitrary feasible witnesses were not exact-matched. Optional prose and sharpness explanations received no semantic score.

There were zero observed substantive financial failures, SQL implementation failures, delivery failures, budget-limit terminations or infrastructure/authentication failures. No new task or grading defect was found in this review. No task, scorer, reference, historical result or prior campaign was revised or rerun. There were no replacements, continuations, hints, grader feedback to candidates or configuration changes between tasks.

## Conditions and observable limits

The starting checkout was clean at `e554adcfdf36088cb507e5beeaf4cfa6d01f8508`. All package, manifest, scorer and SQL-worker hashes match `workflow-hard-pilot-v1-canonical-39c72d97a4ed`. Both execution conditions and all six slot identities were frozen before inference in local checkpoint `0011a43e29247a652df4d4a070c19092806b2351`, execution `hard-calibration-5e1f247e241f`.

| Setting | GLM | Sol |
| --- | --- | --- |
| Native agent | Harbor 0.23.0 Terminus-2, qualified LiteLLM Chat Completions | Harbor 0.23.0 Codex adapter |
| Requested identity | `openrouter/z-ai/glm-5.3`, only `wafer/us` | `gpt-6.1-sol` |
| Observed identity | Responses: `z-ai/glm-5.3` / Wafer. Generation records: `z-ai/glm-5.3-20260816` / Wafer | Native session metadata: `gpt-6.1-sol`, provider identifier `openai`, client `0.162.0-alpha.17.2` |
| Serving quantization | Wafer endpoint advertises FP4, unchanged from qualification | Undisclosed |
| Authentication | Existing dedicated OpenRouter key, unchanged non-resetting USD 20 limit | Native `CODEX_AUTH_JSON_PATH`, existing ChatGPT subscription, no API key or paid API fallback |
| Reasoning | High on every observed outgoing request, interleaved reasoning preserved | High in each native turn context |
| Candidate wall limit | 3600 seconds | 3600 seconds |
| Turns | 24 Terminus-2 turns | No supported Harbor Codex turn cap, none claimed |
| Context | 65536 input-token metadata | Native 500000-token metadata, observed usable context 475000 |
| Per-call output | 16384 requested tokens including reasoning | No supported equivalent cap in the native adapter, none claimed |
| Compaction | Summarization disabled | Native automatic-compaction defaults retained, zero observed compaction events |
| Cache | Full-response replay disabled, provider prefix caching permitted | Native/provider defaults, cached input measured where reported |
| Trial retries/concurrency | Zero whole-trial retries, one trial at a time | Zero whole-trial retries, one trial at a time |

The identical task inputs, output contract and candidate wall limit do not make the agents identical. Their prompts, tools, context behavior, output controls, caching and authentication routes differ. Sol session identity is client-visible metadata, not independent attestation of the provider's backend revision. Neither condition independently attests provider-internal reasoning effort.

Qualified GLM within-request behavior was preserved: the native LiteLLM call and Terminus query layers each retain their existing three-attempt decorators, plus native output-limit recovery. All 21 observed requests returned successful generations. There were zero observed failure events, identical-full-body repeats, length terminations or output-limit recovery calls. Underlying SDK retries remain unknown. Sol recorded one started and completed native turn per task, no error or failed-turn events and no compaction events. Its underlying request retries remain unknown. Native and provider cache/retry observations are not exhaustive internal telemetry.

## Timing, tokens and charges

Agent time is the native agent-execution interval. Controller wall time also includes setup, materialization and verification, so installation overhead is visible separately. No attempt approached its 3600-second candidate limit.

| Condition/task | Agent seconds | Controller wall seconds | Input tokens | Cached input subset | Output tokens | Reasoning output subset | Actual OpenRouter USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM a01 | 176.9 | 242.1 | 54,081 | 40,128 | 23,725 | 20,345 | 0.037447271 |
| GLM b01 | 83.9 | 148.4 | 53,167 | 38,528 | 10,280 | 6,640 | 0.018553665 |
| GLM c01 | 370.9 | 435.6 | 109,766 | 88,864 | 50,876 | 44,113 | 0.079809050 |
| GLM total | 631.7 | 826.1 | 217,014 | 167,520 | 84,881 | 71,098 | **0.135809986** |
| Sol a01 | 74.5 | 201.6 | 83,187 | 30,976 | 3,324 | 288 | Not applicable |
| Sol b01 | 85.2 | 211.6 | 89,021 | 81,920 | 2,431 | 223 | Not applicable |
| Sol c01 | 106.5 | 234.6 | 80,468 | 63,744 | 3,517 | 474 | Not applicable |
| Sol total | 266.2 | 647.8 | 252,676 | 176,640 | 9,272 | 985 | Not applicable |

Cache and reasoning columns are subsets already included in input and output. Sol reported zero cache-write tokens. Its usage totals agree between native completed-turn output and retained session token events. Cross-runtime token and timing measurements are descriptive observations, not a controlled efficiency ranking.

Actual OpenRouter charges total **USD 0.135809986**, matching all 21 generation records and the overall key/account usage movement. Remaining key allowance and funded balance are **USD 7.158229449** under the unchanged non-resetting USD 20 limit. The first a01 closing counter snapshot lagged its response costs by USD 0.010176913. The next scheduled GLM preflight includes that settlement. Both the immediate and settled deltas remain in a01's receipt. No billing history was rewritten. The previously documented historical USD 0.006504900 gap is separate from this experiment.

Sol used the existing subscription. Its observable usage is 252,676 input tokens, 9,272 output tokens and the retained native rate-window records. The displayed 10080-minute window stayed at 36% used across all captured observations. That coarse shared counter does not measure zero attributable consumption or support a precise quota delta. **An actual per-experiment subscription charge is unknown.** No API-equivalent estimate is presented as a subscription charge. No credits, paid overages or funding changes were enabled.

## Isolation, evidence and limitations

Execution ran locally on the Mac Pro (`MacPro7,1`) in the existing dedicated WorkpaperBench Linux guest. Candidate environments and sessions were fresh. Only canonical instructions and dossier material entered the task environment. Worked references, solutions, controls, gold, verifier code, repository history and unrelated files stayed outside it. Personal instructions, configuration, memories, plugins, sessions, skills and MCP servers were not transferred. Sol's fresh native home disabled project-document loading, memories, apps, plugins and multiple-agent features, with web search disabled.

All 30 materialization-integrity records pass. Candidate input checks precede the first observable request/session. All six separate verifiers confirm blocked network, no inference credential and no Docker socket. Credentials were delivered only through the selected native mechanism. Native candidate tools may be able to read that mechanism's credential, including the injected Codex authentication file. This is not secret isolation from candidate terminal tools.

Raw native traces, provider request/response logs, exact commands and funding snapshots remain local. The retained workpapers, receipts and configuration/report outputs contain no detected authentication credentials or account identifiers. Native containers and temporary subscription-authentication directories were removed. The guest retains its initial Running state.

The software verification and this calibration do not replace independent human financial/source review or external-user validation, both still pending. Microsoft's proxy and residuals use rounded source values and an explicit depreciation-scope convention. Apple's sharp bounds depend on the authored uncertainty set, loss rates and constant category-margin assumption. Ahold retains reported FX and the source pro forma perimeter. Issuers overlap historical development material, and no contamination-free claim is made.

Retain the frozen designs for their demonstrated financial and recomputation coverage. These configurations both reached the ceiling, so the experiment does not support retaining a claim of measured harder difficulty. Before a future harder-tier claim, supplement the evidence with independent human/source review and separately frozen tasks or structured analytical obligations that test the intended additional difficulty. No such expansion or additional trial is part of this experiment.
