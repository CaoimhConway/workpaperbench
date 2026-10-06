# Research Challenge contract

The new suite measures research over compact frozen dossiers, separate from the published Core Regression suites. There are three development cases, followed only after calibration by nine evaluation cases. Development and evaluation share no issuer/protocol/source-window group. Nine evaluation cases must have at least six independent source groups. Repetitions and controls are not independent base cases. Common SEC delivery and repeated report templates are disclosed provider overlap.

## Predeclared scoring

Scorer `challenge-1.0.0` has four independent component checks. Financial-answer correctness includes every requested number, status, unit and original-dossier conclusion verdict. Evidence checks reviewed section paths, including compatible scope and definitions. Robustness requires original-input replay and every task-local synthetic control for every answered numerical claim. Delivery checks the bounded JSON contract. Reason codes are optional and unscored.

Verified Research Completion requires financial-answer, evidence and robustness all true. Strict delivery completion additionally requires delivery. Component rates use assessed verdicts as denominators. Completion uses all scheduled attempts, including visible missing outcomes. All cases have three repetitions per model, so scheduled task-macro completion equals the equally weighted per-case rates. Repetitions and source-related cases are not independent problems.

Structural rejection never executes SQL. It leaves unassessed components null. Any single finite scalar SQL column alias is accepted. SQL remains read-only, bounded and executed in the separate native verifier only. No incorrect formula is repaired, missing quantity inferred, duplicate claim selected or favorable retry allowed. Equivalent evidence paths are reviewed before exposure. Section matching checks declared support requirements and does not certify arbitrary free-text semantics. Conclusions are limited to the explicit original-dossier proposition. There is no scored free-text narrative.

## Comparison and exposure

The initial pilot is three development cases times two models times three fresh attempts, 18 full-dossier runs. Models are `qwen/qwen3.6-35b-a3b` and the tool-capable reference `google/gemini-3.1-pro-preview`, through native Hermes/OpenRouter. Cheapness does not establish weakness and the reference designation does not promise a ranking. Both get identical full dossiers, neutral instructions, public checker, native tools, runtime pin, 600-second solve limit and 1,200-second setup limit. Native Hermes retains its 90-turn configuration and provider defaults, including provider retry behavior. Model routes and preview revisions can vary. Current endpoint/price snapshots are in `datasets/challenge-v1/models.json`.

Existing prompt-arm skill experiments remain historical. They are not the intervention here. No expert-selected-evidence diagnostic has been scheduled. If used, it must be a separately frozen assisted condition, development only, with no new facts or gold calculations. It is not main performance or a unique causal identification.

Started slots are never relaunched for a better score. Setup/transport failures remain scheduled missing outcomes, with exact attempt receipts. Read-only GitHub requests may retry transient server failures up to three times. Native provider retries belong to the original slot and lifetime accounting. A bounded native three-hook observer retains content-free request-ID hashes, counters, timestamps and status flags in each new slot record. Repeated pre-request hooks for one logical request count additional attempts, including recovery paths that reset the retry counter. Registration is checked before inference. Hermes hooks fail open, so a captured ledger does not guarantee complete retry history. Capture limits, missing or invalid telemetry are explicit. The ledger is candidate-accessible best-effort telemetry, not tamper-proof evidence. Provider-internal routing and retries remain unobserved. The pinned OpenRouter client disables SDK-level retries. Actions reruns are rejected. Every dispatch rechecks provider lifetime metadata, the unchanged lower cap and the entire remaining-stage reservation. The lower actual dedicated limit is USD 20, below the user's USD 50 ceiling. No top-up or reset is permitted. Inference, Docker, Harbor and untrusted replay run only on Actions.

The final showcase rule is fixed before exposure. Follow the frozen schedule and choose its first delivered answer with a financial-answer or robustness failure. If none exists, choose its first delivered evidence failure. Contrast it with the first verified completion for that case, or the first verified completion elsewhere when the case has none. If there is no substantive failure, show the first verified completion and disclose saturation or missing coverage. Delivery-only failures are labeled separately. No failure is invented and model ranking does not determine selection.

## Practical paths

The key-free local demo reads a reference and evidence without executing submitted SQL:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/workpaperbench demo
.venv/bin/python scripts/build_challenge_tasks.py --check
.venv/bin/workpaperbench report --dataset challenge-v1
```

Key-free native controls, on a maintainer repository or enabled fork:

```sh
gh workflow run ci.yml --repo YOUR_LOGIN/workpaperbench --ref main -f integration=true -f dataset=challenge-v1
```

Commit a bounded workpaper under `submissions/` and use the existing Actions path:

```sh
gh workflow run ci.yml --repo YOUR_LOGIN/workpaperbench --ref main -f integration=false -f fresh_replay=true -f dataset=challenge-v1 -f answer_path=submissions/reference-a01.json -f task=a01
```

Fresh retained replay uses `replay_slot=all` or an explicit retained slot, with `answer_path` omitted. It executes new native verifier trials and preserves old receipts. These new challenge commands are implemented but hosted validation is pending.

Authoring uses `datasets/challenge-v1/authoring/a01` as a native example: factual extracts and capture metadata, concise question, ordinary SQLite tables, private-to-candidate reference/gold, Decimal reference checks and 2-4 task-local controls. The builder reconstructs the package offline. No arbitrary submitted Python executes. Candidates receive only six allowlisted workspace files and instructions. Authoring, references, tests, checkout, history, GitHub keys and Docker sockets do not enter candidate images. Source refreshes and future-model runs require new manifest identities, never frozen-hash bypasses. A future run uses a separate model manifest. Copy `config/challenge-models.example.json` to a repository-local JSON file and select currently compatible native OpenRouter profiles. Then run `python scripts/new_challenge_campaign.py path/to/models.json`. It verifies the unchanged source/scorer freezes and prints new development and evaluation identities, stored as `datasets/challenge-v1/manifests/STAGE-HASH.json`. Commit those files and dispatch `benchmark.yml` with the printed identity, `mode=pilot` or `mode=final`, and `batch=all`. Models must match across that new run's stage manifests. Existing records and identities remain unchanged. These are repeat runs of published cases, not newly held-out evidence. Live dispatch requires a main-branch Linux Actions run and the repository's dedicated capped `OPENROUTER_API_KEY` secret. Forks query their own Actions history. The key's lifetime limit must be no greater than USD 20 and sufficient funded remaining credit must cover the schedule.

## Limits and source rights

Factual numerical observations are retained with source locators, retrieval time and hashes. Full copyrighted issuer documents remain outside the published bundle. Historical observations retrieved now are not automatically point-in-time data. Brale report signatures are distinct from unknown publication timestamps. Its June examiner scope differs from May. The ratio comparison does not establish identical assurance, liquidation proceeds or actual redemption outcomes.

The native candidate can read its dedicated capped inference key. TCP restrictions retain DNS/ICMP channels. The separate verifier has no inference key, network or Docker socket. Screening is bounded and cannot guarantee detection of arbitrary credential obfuscation. A few controls do not prove universal generalization. No measured challenge coverage or discriminating difficulty is claimed before actual runs.
