# Build status

Specification: v3.1. Started 2026-10-04 (America/Los_Angeles).

- Repository: https://github.com/CaoimhConway/workpaperbench; newly created private;
  verified API login `CaoimhConway` (ID 55163829), default branch `main`.
- Development software built for wp01/wp02/wp05. Local install/demo and 55
  lightweight checks pass. Full native development controls passed on Actions.
  Paid trials are still unrun.
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

Stage 1 local implementation and full native development integration: complete.
Latest native namespace smoke: complete. Development pilot: running. Stage 2 expansion/freeze: pending.
Stage 3 audit/campaign/release: pending. No results or completion claims.

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
