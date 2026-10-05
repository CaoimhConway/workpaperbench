# WorkpaperBench — v3.1 implementation specification

**Reviewed 4 October 2026. Status: build specification; no benchmark experiment completed.** Supersedes previous packs and their task assignments. The name stays `WorkpaperBench` / `workpaperbench`.

## 1. Positioning and intended contribution

**Public headline:** WorkpaperBench — Reproducible evaluations for financial research agents.

**Reader-facing question:** Can an agent calculate the right number—and support the conclusion?

**One-sentence description:** A small task suite testing whether agents use compatible financial evidence, produce replayable calculations, and make conclusions supported by the supplied data. The reference run uses Hermes Agent over frozen tables and source excerpts.

Use the headline above in the repository About field and README. “Correct math, unsupported conclusion” is a possible finding or motivating example, not a presumed experimental outcome. Keep the name; do not run another naming or project-selection exercise.

**Question:** Can an agent identify what a financial metric actually measures, make valid comparisons, and leave source-backed, replayable work—or correctly explain a specific evidence limit?

The primary technical audience is an agent-evaluation/research engineer; the flagship workflow is stablecoin/on-chain measurement and financial-data comparability. Build a small regression suite plus a useful source-linked case study, not a general financial benchmark or AI analyst. The suite should make it easy to reproduce a meaningful failure, inspect a valid alternative and evaluate one targeted change.

The public Artemis methodology note supplies a real example of changing transfer-volume semantics and distinct delivery surfaces [R1]. It does not establish an Artemis bug, a discontinuity in its historical series, or a failure of its AI product. The project is not endorsed by Artemis or Nous. We evaluate Hermes Agent with a declared underlying model, not either company's private production stack.

**What makes the release worth reading:** a concrete measurement question; preserved evidence; inspectable graders; actual agent behavior; one justified intervention; and an honest account of remaining failure or a null result. A large score, promised uplift, CEO endorsement or merged PR is not a requirement. Do not wait for external feedback to build.

## 2. Hard scope

| Decision | Limit |
|---|---|
| Tasks | Exactly 8: development wp01/wp02/wp05; evaluation-not-tuned wp03/wp04/wp06/wp07/wp08 |
| Work | Curated local tables, source excerpts, and explicit metric contracts; no open-web research during scoring |
| Output | One `answer.json` with numerical answers, evidence IDs and SQL; optionally one task-required bounded conclusion |
| Harness | Native Harbor task packages + existing Hermes integration + separate verifier |
| Inference | One current hosted tool-capable model, selected autonomously before evaluation |
| Treatment | One small skill OR one small existing-data presentation helper, chosen from development observations |
| Live work | Up to 12 exploratory slots; 48 fixed final slots (8 × 2 × 3) |
| Execution | GitHub Actions Linux VM; no local Docker/GPU requirement |
| Deliverables | Offline demo, task pack, tests, sanitized reproducible results, README, one case study |

No app/server/UI, local model, new agent adapter, LLM judge, arbitrary submitted-Python runner, vector store, multi-agent system, distributed scheduler, generic metric ontology, SQL parser, multichain indexer, scraping framework, billing service or account-management framework. No third workflow or separate deployment. Do not add models/tasks after seeing final scores.

## 3. Task briefs

Task IDs keep their v3 meanings. This review swaps wp03 and wp05 between development and evaluation before any implementation/model run; it does not add tasks. Prior v2 meanings of wp04–wp08 remain retired. Candidate filenames must not reveal the gold verdict or split. At most four numerical answers and one conclusion per task. Inputs should fit a short analyst work session, not a hidden puzzle. Numerical precision and requested units must be explicit.

| ID | Split and origin | Required work |
|---|---|---|
| wp01 | Development, Tesla primary filing | Derive Q1 R&D from H1 and Q2, then Q2 sequential change. A pipeline smoke test, not the flagship. |
| wp02 | Development, authored ledger | Deduplicate copied export records using event identity while retaining distinct events in one transaction. Exclude explicitly identified mint/burn events. Compute transfer total. The bounded positive proposition is that distinct eligible events in one transaction must both contribute under the supplied event-based definition; author a fixture that supports it. |
| wp03 | Evaluation, authored dated releases | Calculate an as-of result from eligible publications, reject a later revision as supporting evidence, and distinguish an unavailable requested input from zero. Supply eligible observations for two comparable periods with genuine growth; the narrow proposition that this defined metric grew on the eligible evidence is supported. A separate requested input is unavailable. This supplies an evaluation positive control without claiming payment adoption. |
| wp04 | Evaluation, small observed USDC log capture where available | Over one fixed Ethereum window, compare all eligible transfer events with keeping only the largest eligible event per transaction. Give both totals and their difference; determine whether this within-window calculation establishes a change in economic activity over time. It does not. Do not call the second total the full Artemis-adjusted metric. |
| wp05 | Development, explicitly synthetic migration case informed by public methodology | Two periods were exported under different definitions. Supplied row-level data and explicit synthetic labels let the agent recalculate both under the SAME requested definition. Report naive cross-definition growth and comparable growth. The bounded proposition is that eligible transfer amount grew on the same supplied definition and coverage; author a modest genuine like-for-like increase alongside a larger misleading headline increase, so this positive proposition is supported without establishing payment adoption. Specify exclusion order and units; no proprietary label reconstruction. |
| wp06 | Evaluation, independent synthetic coverage/joins case | A feed expands its covered asset/network population. Compute reported total growth and matched-coverage growth, avoiding inflation from a one-to-many metadata join. Assess the narrow claim that the reported change equals like-for-like growth. Avoid causal claims about individual users. |
| wp07 | Evaluation, Apple primary filing | Derive first-fiscal-quarter Services revenue/gross profit from cumulative amounts, then margin and Q2-minus-Q1 percentage-point change. Tests transfer beyond crypto without dominating the project. |
| wp08 | Evaluation, observed corpus shared with wp04 plus explicit missing-label task | Compute an observable transfer statistic but decline business-payment volume/unique-human counts not identifiable from these logs. Assess whether the observable proves the specified payments claim. Require a supported numerical answer AND a specific evidence limit. |

**Build order:** wp01 is the integration smoke test; wp02 and wp05 complete the development slice. Observe the metric-definition/migration workflow before selecting the intervention. Build wp03/wp04/wp06/wp07/wp08 afterward; no scored-model execution on them before freeze. Task numbers are identifiers, not build order.

Sharing wp04/wp08's source is intentional: they test different operations over the same corpus. Mark the source group and do NOT call five evaluation tasks five independent datasets. The synthetic cases share conceptual families with development tasks; this is a small regression study, not a contamination-proof benchmark. Labels in synthetic data are authored ground truth, not discovered wallet attribution.

### First source-backed values

Recheck source headers and context before authoring; these planning figures are not finished assets:
- wp01: Tesla Q2 2024 R&D = USD 1,074 million; H1 = 2,225; Q1 = 1,151; sequential change ≈ -6.6898349% [R2].
- wp07: Apple FY2024 Q2 Services six-month / three-month revenue = 46,984 / 23,867; gross profit = 34,646 / 17,809, USD million. Derived Q1 revenue = 23,117, profit = 16,837; Q1 margin ≈ 72.8338%; Q2-minus-Q1 ≈ 1.7838 percentage points [R3].

### Bounded observed-log acquisition

Do not build an indexer. Obtain one historical Ethereum USDC `Transfer` log capture plus relevant block identities and contract metadata. Default request: blocks **20,000,000–20,000,031**, chain 1, Circle's documented Ethereum USDC address `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`; validate the standard `Transfer(address,address,uint256)` topic/ABI and units from primary sources [R4–R6]. Preserve complete returned events for the stated window, event identity `(chain_id, block_hash, log_index)`, transaction hash and capture metadata. Keep block identities already present in log records and acquire boundary headers/contract metadata within the request budget; do not make one header request per event. No source keys in URLs/manifests. Store amounts as integer base units with an explicit decimal scale; bound sums before SQLite use. No generic uint256 subsystem.

Try the documented PublicNode endpoint and, only if necessary, one other currently documented public RPC or an authentic public export of the same window. Respect limits. Maximum six bounded requests per acquisition path, with normal rate-limit backoff. Run network-bound capture on Actions when the local agent sandbox cannot reach it. The source need not contain a desired failure or a desired difference: keep it even when the two aggregates coincide. No cherry-picking blocks based on model performance.

If complete observed logs cannot be acquired lawfully after those attempts, use one clearly synthetic shared corpus for wp04/wp08, record the downgrade, and finish the software. Do not invent a real capture or keep adding providers. The public case study must disclose the downgrade and must not claim empirical on-chain behavior. This is a materially weaker empirical case, not an invisible substitution.

Public methodology defines a motivating problem, not historical numeric snapshots. wp05's numbers and labels remain synthetic even when motivated by a real documentation change. Never suggest a gross transfer is necessarily a payment or a dollar; use token units without supplied valuation data.

## 4. Packaging and provenance

Each native task provides `data.sqlite`, `evidence.json`, concise source excerpts/data dictionary, instructions, and the same public schema/checker in both arms. Write candidate instructions as ordinary work requests, not copies of the authoring briefs: specify the required question, units, cutoff and output but do not announce the expected verdict, relevant pitfall or correct query. Put the actual definitions in the source material where an analyst can find them. Do not hide necessary information or add ambiguity to manufacture failures. Build SQLite deterministically from small committed CSV/JSON with a task-local schema. Preserve plausible context/distractors, headers, time/units and exclusions; do not encode gold selection in input filenames.

Each source record has its original URL or synthetic origin, available publication precision, economic period/block window, retrieval time, content/derived hashes, and redistribution decision. Maintain one `DATA_SOURCES.md`, not a rights-management system. Default code license MIT; only license original task annotations/fixtures as your own. Public access is not blanket permission to redistribute every embedded issuer document. Permitted factual extracts plus full source locators are sufficient; do not bundle private/uncleared source files. Inputs must run offline after acquisition.

Changed-input SQL control fixtures are separately labeled synthetic tests, even for a real-source task. Never modify a frozen real capture and retain its original provenance label.

Gold and reference calculations live only in task solution/tests or trusted grading. They may be public in the repository but are excluded from candidate images, mounts, archives and network access. Never stage the full checkout into a task image.

## 5. Output contract

The candidate publishes one bounded regular file at `/logs/artifacts/answer.json`. Example only (authored; not a live result):

```json
{
  "task_id": "wp02",
  "answers": [
    {
      "id": "transfer_total",
      "status": "answered",
      "value": 1250,
      "unit": "token_units",
      "evidence": ["ledger:events", "policy:transfer_definition"],
      "sql": "SELECT SUM(amount_units) AS value FROM (SELECT event_id, MAX(amount_units) AS amount_units FROM events WHERE event_kind = 'transfer' GROUP BY event_id)",
      "reason_code": null
    }
  ],
  "conclusion": {
    "verdict": "supported",
    "reason_code": "supported_by_calculation",
    "evidence": ["ledger:events", "policy:transfer_definition"]
  }
}
```

`conclusion` is null unless the task requires a verdict about one clearly worded proposition. All tasks receive the SAME public output schema and complete small reason-code vocabulary; only requested claim IDs, units and proposition differ. Do not give one task a singleton list containing its correct explanation. Verdicts are `supported`, `contradicted`, `not_established`. Their meaning is scoped to THAT proposition and supplied evidence, not general financial truth. Development wp02/wp05 and evaluation wp03 support their stated narrow claims by design; retain positive controls in BOTH splits so “not established” is not universally optimal. wp01/wp07 can require no conclusion.

Use this flat conclusion-code list everywhere: `supported_by_calculation`, `contradicted_by_calculation`, `incompatible_definition`, `incompatible_coverage`, `ineligible_source`, `missing_required_evidence`. Use this flat numerical-unavailability list everywhere: `no_eligible_observation`, `missing_comparable_definition`, `missing_required_labels`, `missing_required_input`. These are simple enums, not an ontology. The trusted task grader maps valid code/evidence combinations to the specific task; accept genuine equivalent codes where they accurately describe the mechanism. A code alone never establishes a correct answer.

Numerical answers have `status = answered`, a finite numeric value (not a Boolean), canonical unit, evidence and a single SQL statement returning one row/column `value`. CTEs/subqueries/joins/ordinary aggregates are legitimate. Unavailable answers have `status = insufficient_evidence`, null value/SQL, canonical requested unit, evidence, and a task-defined missing-input reason. Missing is not zero. Exact field/claim sets, no duplicate JSON keys, and no extra answers. Order is immaterial. No free-form rationale is scored.

Task-local grading and rendered context describe the specific mechanism behind a shared reason code. Accept genuine equivalent evidence sets and numerical tolerances. A valid URL/ID is not by itself adequate support; review required operands/context and reject unrelated/citation-dump submissions. Structured source-linked findings do not claim to recover the model's private reasoning.

**Pre-freeze leakage review:** give a fresh read-only reviewer, when available, just the candidate instructions/schema—not source tables or reference answers. Inspect whether labels, narrowed code choices, worked examples or filenames give away the intended answer. Fix accidental solution hints before freeze, while retaining legitimate task requirements. This is an authoring review, not an extra scored model baseline or a proof of no leakage. Computation/comparability tasks must require the evidence; some evidence-limit questions can be partly inferred from the dataset's declared scope, and the report must not overstate their difficulty. Examples must be generic and must not contain any real task's answer.

## 6. Grading invariants

1. **Frozen evidence:** changed input hashes fail validation; never silently refresh sources.
2. **Context before scalar:** correct entity, time eligibility, period, definition and units matter alongside arithmetic.
3. **Evidence actually supports the bounded claim:** use reviewed operand/evidence groups and task-local verdict rules; no general semantic-verifier claim.
4. **Real recomputation:** replay the same SQL on pristine inputs AND a small declared schema-compatible changed-data fixture. A hardcoded scalar or a table mention that ignores data must fail. Do not claim the fixture proves every arbitrary program generalizes.
5. **Trustworthy isolation:** native separate verifier; no inherited candidate filesystem, gold access, host mounts or submitted database.
6. **Fresh trials:** no cross-trial sessions/memory/learned skills; reuse immutable dependencies only.
7. **Valid alternatives pass:** test CTE/subquery equivalents, supported evidence alternatives and documented tolerances.
8. **Insufficient is distinct from false:** not established is not disproven. Blanket refusal and blanket skepticism must fail answerable/supported cases.
9. **Grader review is part of the product:** independent direct source calculations, known-good and plausible-wrong controls, including a correct scalar with wrong context.
10. **Accounting is complete:** every scheduled slot stays in results; failed/cancelled/invalid/infra runs never disappear or become free retries.
11. **One controlled difference:** same task data/instructions/schema/model/resources, with exactly one frozen treatment; disclose any remaining provider variation.
12. **Bounded claims:** show partly synthetic origins, shared sources, development exposure, agent-only review and any untested behavior.

Strict task completion requires every requested numerical/evidence/replay/availability/conclusion check. Diagnostic checks remain visible; nice formatting cannot compensate for a wrong metric. For each task, test at least two valid alternatives where meaningful and three plausible wrong submissions. Add named controls for always-abstain, all-citations, constant SQL, period/definition mismatch, and tampering.

### SQL boundary, deliberately small

Use Python stdlib SQLite with `mode=ro`, `query_only`, disabled extension loading, a restrictive authorizer allowing only the necessary read/query operations and functions, and no attached databases/filesystem/pragma escape. A killable subprocess receives ONLY SQL and pristine input paths, never gold or inference credentials. Launch the worker from a trusted directory with isolated Python import behavior; never put submitted paths on its module search path. Trusted comparison of its bounded JSON output happens in the parent. Set statement/artifact/result limits, an SQLite progress handler, OS memory/CPU limits on Linux, and a wall timeout. Suggested starting limits: 64 KiB artifact, 16 KiB per SQL, 2 seconds/query, 256 MiB worker; revise only from legitimate control tests, before freeze. A `SELECT` string prefix is not security.

Separate verifier plus the authorizer are complementary. Test denied writes/ATTACH/load_extension, oversized output, nonfinite values, pathological recursive queries, symlink/nonregular artifacts and candidate source tampering. Do not execute/import candidate Python, candidate modules or candidate databases. Native Harbor artifact copying must not overwrite trusted test/data paths. The supported output is one file; reject unexpected transferred content before trusted execution. Do not implement a general sandbox platform.

## 7. Execution and code shape

Use Python, stdlib SQLite, one schema library, pytest, uv, Docker on Actions, and native Harbor/Hermes. Pin a tested compatible Harbor version and Hermes revision, plus Python/base image; record actual runtime versions. The native installed Hermes adapter forwards the inference key into its agent environment [R7]. Do not assert that arbitrary terminal code inside that environment cannot access it. Permit only the dedicated capped inference key there; never include GitHub credentials, other provider credentials, gold or host sockets. The separate verifier and replay worker must receive no inference key. Inspect the pinned adapter and document this limited trust boundary; do not build a credential proxy/new adapter to claim stronger isolation. Verify pin effectiveness, not merely a config string. Current upstream installation behavior may use network/bootstrap scripts; record residual moving parts rather than claim bit-for-bit reproducibility [R7]. Keep install/setup time separate from task-solving time.

Use ordinary small modules for schema/grading, SQL worker, reports/CLI, and a thin native-run driver. CLI needs only `validate`, `demo`, `report`; a straightforward script invoking native Harbor for scheduled slots is sufficient. No generic runner interface or retry engine. The driver handles budget preflight, one scheduled invocation, sanitized record generation and status—not a new agent stack.

`demo` must be lightweight, container/key-free, using trusted authored output. It is NOT a host path for executing arbitrary live-agent artifacts. Full hostile-output replay and container verification run in Actions. Downloaded live results can be viewed or structurally inspected locally; replay them remotely.

Exactly two workflows at completion: `ci.yml` (uncredentialed unit/reference/integration) and `benchmark.yml` (explicit dispatch, paid). Implement the contract in `build-notes/ACTIONS.md`. All heavy tests/run commands in README must have a `gh` path usable from this weak device. No requirement to install Harbor locally merely to inspect the project.

## 8. Observe, choose, freeze, measure

**Exploration:** after wp01/wp02/wp05 and graders work, run baseline development tasks, including the migration case. Inspect actual recorded failures. Correct broken plumbing first. Up to 12 exploratory live slots total, including compatibility probes. Choose at most one skill of roughly 150–300 words OR a small (roughly ≤80 runtime lines) tool/data-card helper exposing metadata already supplied to both arms. Do not inject answers, task IDs/formulas or newly privileged evidence. The treatment may be a disciplined contract check when no substantive failure is found, but call that hypothesis unconfirmed; do not invent a diagnosis. Do not require an upstream code change. Record a brief pilot diagnosis in BUILD_STATUS.md: substantive measurement issue, evidence-selection issue, output/runner defect, or no observed failure. Fix unfair prompts/graders/infrastructure before interpreting model weakness. Do not choose a weaker model, inject ambiguity or expand the task list to force a striking failure. Finish the bounded experiment with a candid ceiling/null report if that is the result.

**Models:** Hermes Agent and a Nous model are different things. Select one available, reasonably priced hosted open-weight model with actual endpoint `tools` support and successful terminal-tool behavior. Use current catalogue + a development compatibility test, not brand association or a desired failure rate. Do not force `hermes-4-405b` just for its name; verify endpoint features. Select/pin automatically. Replace a non-working endpoint only before freeze, retaining the failed setup record. No free/auto-router/latest alias for the final comparison when a stable explicit identifier is available.

**Freeze:** source/task/grader hashes, development/evaluation/source-group manifests, model identifier/route, versions, toolsets, prompt/skill/helper hash, limits, scheduled slots, retry rule and budget. Freeze before ANY evaluation model attempt. A new agent session does not reset development exposure or spending.

**Final 48 slots:** 8 tasks × 2 arms × 3 attempts. On each task/repeat, alternate A/B versus B/A using a fixed declared parity rule. Repeats use fresh state. Main table: **30 evaluation slots**. The 18 final development slots and ≤12 exploratory slots are separately labeled. No best-of-three, model leaderboard, statistical-significance claim or treating related cases/repeats as independent.

A = full common requirements/checker. B = A plus exactly the frozen treatment. Same tools except the explicitly declared helper if that is the sole treatment. Do not change model limits/routing/data at the same time. Record effective native toolsets and whether delegation/memory/network tools are enabled. Prefer terminal/file/skill functionality only; no subagents or internet research during solving.

Run serially. Persist a record before and after each slot. Disable outer automatic trial retries for final scored slots. SDK transport retries remain part of the original slot and cost; record where exposed. Infrastructure failure remains visible in the schedule; any justified rerun is supplemental and never replaces the first score. Regrade both arms' saved output after a grader correction; preserve the old verdict/version. Changed task instructions/inputs invalidate affected comparisons and need an explicitly new run version, not selective erasure.

Use the standing cost policy in AGENTS.md. OpenRouter's non-resetting dedicated-key limit is the cross-job budget backstop, not a local file reset. Check current key metadata before/after calls; do not print sensitive metadata. Store only usage/cap/remaining fields needed for the report. Disclose estimated versus provider-reported costs, lag and unknowns. Stop before the next trial when remaining credit cannot safely cover it. No custom payment service.

## 9. Report and release

Generate `reports/results.md` and machine-readable scores from persisted records, not hand-entered totals. Show each task/arm/repeat, failure checks, run IDs/config hashes, origin/source groups, runtime errors, observed latency and cost. Include all paid failures in cost per verified completion; zero completions is not zero cost. A partial campaign is partial, not a finished 48-slot experiment.

Promote existing diagnostic checks into a compact visible breakdown: expected numerical values correct, evidence/context checks passed, conclusion correct where required, replay passed, and strict verified task completion. Show the observed cross-tab “numbers correct but full task failed,” with the reason split into substantive evidence/context/conclusion, calculation-replay, and format/infrastructure problems. Do not describe a JSON-schema failure as faulty financial reasoning. Use the same declared scheduled-slot denominator for task-level rates; no eligible numerical/conclusion claims means N/A, not automatic success. Retain invalid/infra slots in completion accounting and display them separately. This is report formatting over existing flags, not a new judge or extra inference campaign. Report zero gap when zero is observed.

Write one `reports/case-study.md`: question → source/metric definitions → actual saved submission → verifier diagnosis → proposed/observed change → limitation. Preferred story is a meaningful comparison/coverage/evidence failure in wp04–wp06/wp08, ONLY when observed. Otherwise lead with the validated workpaper and honest null/ceiling result. A wp05 development finding must be labeled development evidence, never held-out performance; prefer a meaningful evaluation-case finding when present. Choose cases by a disclosed deterministic priority (measurement error, then evidence error, then plumbing; include a regression when present), not only favorable runs.

README starts with the public headline/question from section 1, then a short measured finding or accurately labeled authored demonstration and the already-rendered workpaper. Show the actual question, source values/definitions, answer, replay calculation and exact verifier diagnosis without requiring a key or container just to read them. Follow with one command to inspect it, scope, tiny results/check-breakdown table, methodology/limits and how to add one native task. Do not build a frontend, recording pipeline or additional demo application. Include an upstream-ready task/failure note only when supported, not a promised merge. No CEO names, hiring pitches, private client material, speculative novelty, or “production-grade” claims in public docs.

**Software-complete:** all eight tasks, verified sources/or explicit downgrade, controls, native isolated container tests actually passing on Actions, tested local demo, tested remote commands, pinned configuration and source/secret audit. The starter Docker preflight alone is not sufficient.

**Empirical-release complete:** software-complete plus the full frozen campaign, preserved/redacted evidence, generated results and candid interpretation. A null result qualifies; missing trials do not. Publish as authorized after the appropriate gate. No external human reviewer is required to finish; clearly label independent agent recomputation as agent review.

## 10. Build stages and no-stall rules

1. Working remote end-to-end path with wp01/wp02/wp05, independent controls, cloud preflight/native isolation, bounded exploration including metric migration, and treatment choice.
2. wp03/wp04/wp06/wp07/wp08, source review, balanced controls, prompt-leakage review, corrected freeze and software publication audit; no model calls on evaluation cases.
3. Independent source-first audit, final campaign, generated report, release.

Implement continuously under AGENTS.md. Missing GitHub login/key blocks remote/paid work only. Public-source access failure uses the bounded documented fallback. Do not wait for a CEO, committee, GUI Docker approval or routine user decision. Do not silently degrade isolation or fabricate empirical completion.

Primary source keys [R1–R19] are in `build-notes/SOURCES.md`.
