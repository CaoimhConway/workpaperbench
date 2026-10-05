# Build status

Specification: v3.1. Started 2026-10-04 (America/Los_Angeles).

- Repository: https://github.com/CaoimhConway/workpaperbench; newly created private;
  verified API login `CaoimhConway` (ID 55163829), default branch `main`.
- All eight packages are authored, with the expanded native gate still pending.
  Development pilot has 11 started slots and one remaining treatment check.
  Latest integrated lightweight suite: 112 checks passed.
- Dedicated key transferred through stdin to `OPENROUTER_API_KEY`. Provider metadata
  checked 2026-10-05 UTC: lifetime cap $20, reset null, usage $0, remaining $20,
  BYOK usage $0. Project authorization ceilings remain $50 inference / $10 Actions.
- Git identity issue resolved with explicit owner authorization: existing work
  include changed to case-insensitive `gitdir/i:~/code/work/` and moved after the
  global fallback. Verified effective work identity. The bootstrap commit
  `da28f4a` used the fallback before the ordering correction. History preserved.
- Initial key-free Docker plumbing preflight passed: Actions `37261618709` on
  bootstrap `da28f4a`. This is not native Harbor isolation evidence.
- Sandbox network access initially made `gh auth status` look invalid; an authorized
  network-enabled API request succeeded. Existing CLI account switched normally.
- No Docker, Harbor or model inference executed on this device.

## Gates

Stage 1 software/native development gates complete, treatment delivery check pending.
Stage 2 sources and controls are being completed before freeze. Stage 3 campaign
not started. Historical observations below retain the failures and superseded pins.

## Development checkpoint

- Native source pins: Harbor 0.23.0 at `1e5c5c6db929a10a140d05e606882c671ae20729`,
  Hermes `v2026.9.24` resolves to `f97608f178d1ffeca59860195ab7da295f7c8e5f`.
  Native installer still fetches upstream main bootstrap and pins a tag. No
  immutable per-container checkout claim until runtime verification.
- Model selected from current OpenRouter catalogue: `qwen/qwen3.6-35b-a3b`,
  open-weight, tool-capable. OpenRouter native default route may vary providers.
  Compatibility and actual tool use remain pilot gates.
- Candidate Python base image pinned by manifest digest in `config/runtime.json`.
  Native toolsets file/terminal/skills, max turns 90 fixed by adapter. Cold setup
  1200 seconds, solving 600 seconds, separate verifier 180 seconds and no network.
- Tesla filing headers and 2023/2024 values independently checked. Synthetic event
  and migration fixtures preserve positive propositions. SQL replay also checks
  explicit synthetic amount changes.
- Tested local: `.venv/bin/python -m pip install -e '.[test]'`, `.venv/bin/workpaperbench demo`,
  `.venv/bin/python -m pytest -q` (51 passed).
- GitHub billing summary unavailable to existing token (404, user scope absent).
  No token scopes changed. Standard private Linux rate currently $0.006/minute.
  Track all project run minutes conservatively against $10 rather than assume
  account quota. Public standard compute is free after the software audit gate.
- Inference usage remains $0. No paid trials dispatched yet.

- Development native integration dispatched: `gh workflow run ci.yml --repo
  CaoimhConway/workpaperbench --ref main -f integration=true -f capture=false`,
  Actions `37263846465`, commit `ca3c61c`. Unit job passed 51 checks and demo.
  Full native controls passed, 27 cases (10 expected completion passes, 17
  expected failures). Sanitized results preserved under reports. Push CI
  `37263842795` also passed.
- Funded credit independently checked at provider `/api/v1/credits`: $20 total,
  $0 used. Added funded-balance checks, synthetic budget/report controls, and
  source-group run metadata. Four new focused controls pass (55 total tests).

- Pre-pilot review accepted genuine operand/context citation alternatives without
  admitting irrelevant or ineligible sources. All 55 local checks pass. The
  updated network probe uses a bounded direct TCP connection. Added per-control
  sanitized artifacts and explicit full/smoke integration labels. Full eight-task
  CI has a 90-minute ceiling based on observed 21-minute development integration.
- Pinned uv 0.9.26 installed and the lightweight dependency command tested.
  Reports retain setup/solve/verifier timing, known/unknown costs and source groups.

- Smoke recheck `37265511360` failed on a bare TCP probe. Source inspection shows
  native Docker TCP is redirected to a local gost filtering proxy, so connection
  establishment is not external egress proof. Replaced the probe with a bounded
  authenticated TLS handshake to a numeric external address. No network policy
  relaxed. Failed native checks now retain their sanitized control record.

- Corrected TLS smoke `37266025062` passed all six native reference/empty controls.
  Harbor Docker filtering permits DNS/ICMP, so the verifier now uses native
  `tests/docker-compose.yaml` with `main.network_mode: none`. Loopback-only
  interfaces and failed external TLS are required. Hosted confirmation pending.
- The native invocation uses `Trial.create` / `Trial.run` and its documented
  AGENT_START hook to verify installed Hermes HEAD before solving. No adapter
  or credential proxy was added. Pin enforcement awaits the development pilot.

- Publication bundles are scanned before and after JSON decoding. A synthetic
  escaped-credential control passes. Local focused checks: four budget/artifact
  controls passed. Provider usage remains $0 before the pilot.
- Completed private jobs through `37266025062`: 33 rounded job minutes, $0.198
  compute upper estimate at $0.006/minute. Included account quota and actual
  invoice charge remain unavailable. Small seven-day artifacts add negligible
  storage at this stage, not a known zero charge.

- Native namespace smoke `37266518124` on `3a87fa9` passed all six controls,
  including loopback-only verifier interfaces, blocked external TLS and absent
  inference key/socket. Permanent sanitized report retained.
- Baseline exploration dispatched on `0c725b5`: Actions `37266930239`, command
  `gh workflow run benchmark.yml --repo CaoimhConway/workpaperbench --ref main
  -f mode=pilot -f batch=baseline -f manifest_id=development-v1`. Slots are
  wp01/wp02/wp05 A1, serial. Outcomes and costs pending.

- Pilot `37266930239`: wp01 A1 and wp02 A1 failed during native installation
  (`NonZeroAgentExitCodeError`), before solving. Both measured provider deltas
  are $0. Canceled the same broken setup before proceeding. Failed slots stay
  recorded. Adding a key-free native install-only diagnostic to inspect the
  controlled installer error without uploading live traces. Treatment pending.

- Key-free installer diagnostic `37267321820` confirms an upstream bootstrap/tag
  mismatch: current main installer requires `pm/lock.json` and `pm.cli`, absent
  from the September tag. All three original pilot slots failed before solving,
  each with measured $0 inference delta. A compatible released tag will be
  checked key-free before supplemental development slots.
- Actions exposes non-null job start timestamps while jobs are queued. Resume
  selection now distinguishes allocation/started steps from a queued timestamp.
  Two focused control-plane tests pass.

- Primary tag/code inspection selected timestamped Hermes canary
  `v0.21.4+canary.20261004T084456Z` at
  `8b66a51036c1e20920a17cdd049fdf55c968d683`, which includes the PM package.
  Stable latest release remains September and is incompatible with today's
  native bootstrap. Retained tested Harbor 0.23.0. Installed checkout location
  follows current installer `/root/.hermes/hermes-agent`. Key-free hosted
  confirmation is required before new pilot slots.

- Canary install checks `37267758153` and `37268139696` isolated a missing
  system library: managed Node requires `libatomic.so.1`. Added Debian
  `libatomic1` to candidate images. No network policy changed. Key-free gate
  rerun required. Six pilot slots are declared: three preserved A1 setup
  failures and three new A2 supplemental baseline slots, not dispatched yet.
- All 58 local tests pass, including decoded-credential and queued-job controls.

- `37268358386`: libatomic fix completed installation, then native Harbor failed
  on obsolete `hermes version`. Current CLI supports `hermes --version`. Applying
  a two-occurrence correction to the existing native adapter, guarded by exact
  original/corrected module hashes. This is a dependency bug fix, with no new
  adapter, proxy or execution behavior. Actual corrected gate remains pending.

- Corrected-version gate `37268809048` found a native setup/runtime data-root
  mismatch. Configured native `agent.env.HERMES_HOME=/tmp/hermes` for both setup
  and solving, which also places the checkout at `/tmp/hermes/hermes-agent`.
  Optional desktop-tool warnings do not require adding desktop dependencies.
- Capture validator now checks boundary numbers, address ABI padding and hashes,
  and records request counts on failed paths. Two synthetic protocol tests pass.
  No source capture has run yet.

- Key-free native installation gate `37269174132` passed on `d7c0517`.
  The corrected native version command and consistent data root are working.
  Independent native solve/tool/model compatibility remains to be observed.
- Dispatched supplemental baseline `37269765974` on the same commit. Resume
  selected only wp01/wp02/wp05 A2, preserving all three A1 setup failures.
  Paid findings, costs and treatment choice pending these observations.
- Supplemental run `37269765974` wp01 A2 installed and verified the exact
  Hermes revision before solving, then exited in 12.864 seconds without tool
  events or an answer. Provider lifetime usage remained $0. This is a runtime
  compatibility failure, not evidence of financial reasoning failure.
- Canceled that run. wp02 A2 had started installation and its uploaded start
  record is retained as an infrastructure failure with unknown slot cost.
  wp05 A2 never received a runner and remains resumable. Five live slots have
  actually started across the two pilot runs. A key-free CLI argument check
  is added before another live attempt. Model-route source inspection ongoing.
- Pinned primary source inspection found native compatibility defects: the
  OpenRouter provider prefix is not a canonical model ID in this Hermes route,
  and finite-query sessions are now labeled `oneshot` rather than `cli`.
  Correcting the existing native adapter's provider flag and export filter,
  guarded by the exact original and corrected module hashes. This preserves
  the selected model, key flow, terminal tools and separate verification.
- Key-free CLI gate `37270674684` passed: model, toolset, finite-query and
  query arguments are accepted. The recorded RuntimeError is the intentional
  hook stop before the native solver, not an installation failure.
- Native corrected module SHA256 is now
  `02ebd73edb387091480df45fdea27b70bf37ca377ee0b68047b84d6cdbede112`.
  Full lightweight suite passed 60 tests, plus a focused new diagnostic
  redaction control passed. Pending baseline slots are wp05 A2, wp01 A3,
  wp02 A3. Their future records will include allowlisted failure codes only.
- Corrected-route run `37271209030` produced real submissions and native
  terminal events. wp05 A2 submitted 65% naive and 10% comparable growth,
  but the old instruction omitted the required task identifier. It guessed
  wp01, causing a format rejection. Both submitted SQL queries also omit the
  explicitly required `value` column alias. Key-usage delta: $0.01121775.
- Independent read-only source review confirmed the missing identifier and
  a valid citation alternative: export:periods alone supports naive export
  growth. Added explicit task identifiers to all candidate instructions and
  accepted that citation set. Comparable growth/conclusion still need the
  counting policy. Added a named valid/invalid citation test and a native
  regrade control preserving the old failed record. These are fairness fixes,
  not treatment or measured financial weaknesses.
- wp01 A3 passed every applicable check with native terminal/file events.
  Key-usage delta: $0.00304445. wp02 A3 remains in progress.
- Three supplemental baselines after the authoring corrections are declared,
  bringing the pilot manifest to 11 slots. One development treatment check
  remains possible inside the 12-slot ceiling. No treatment is chosen yet.
- Completed private Actions accounting through the earlier snapshot: 88
  rounded minutes, $0.528 compute estimate before included quota. Invoice and
  storage charges remain unknown. A post-dispatch metadata-only job will
  reconcile lifetime usage without additional inference.

- Corrected-route pilot wp02 A3 failed the output contract despite computing 1200: extra claim, prose evidence and missing SQL column alias. Baseline run `37272511333` finished wp01 A4 complete, wp02 A4 contract failure, wp05 A3 numbers correct/full failed. The migration submission used hardcoded naive-growth SQL and prose evidence IDs. Its comparable SQL and 10% scalar were correct. No substantive financial miscalculation is inferred from those failures.
- Chosen intervention: one 230-word contract-check skill, aimed at requested fields, exact evidence IDs and data-dependent SQL. Its causal benefit is unconfirmed. Both final arms receive the same explicit common contract. One B delivery check on wp05 brings the exploration manifest to the 12-slot ceiling. No further exploratory calls are allowed.
- Added native pre-solve assertions for the exact skill text in the instruction and its staged file hash. Actual delivery remains a hosted gate. Native zero token fields are recorded as unreported rather than measured zero usage.
- `37272514161` passed the six native development smoke controls. Canonical sanitized pilot bundles and integration result are retained. Reconciled provider snapshot `37272511333` reports lifetime usage $0.06977975, remaining/funded $19.93022025, cap $20, reset null and BYOK usage zero. Per-slot snapshots lag and are not the total-spend authority.
- Bounded capture `37273047665` tried the fixed window through PublicNode (one request, HTTPError) and documented Cloudflare (one request, RPC error). Both failed. Applied the authorized synthetic shared-corpus downgrade to wp04/wp08, retaining the acquisition failure record. No observed on-chain amounts or behavior are claimed.

- Treatment delivery check `37274770675` completed wp05 B1 with every check passed. Before solving, native runtime HEAD matched and both treatment instruction presence and staged skill SHA256 matched `651820768f6a80222f92256abd9ac58474a480fcfbdf212bda8b22fff1863bb0`. Recorded slot cost delta $0.0062061 is provisional. This exhausts the 12 exploratory slots. Pilot results do not establish causal uplift because common authoring corrections preceded the delivery check.
- All eight tasks have explicit origin metadata. Fresh read-only source-first audit found that the previous fallback would incorrectly label wp03/wp06 as primary filings. Fixed before any evaluation execution. The dated-release catalog now rejects the late publication by its own source ID while accepting eligible preliminary context.
- Source review, instructions/schema-only review and named evaluation controls are preserved in `reports/source-review.md` and tests. Local full suite passed 122 controls. All-eight native integration and final freeze remain pending.
