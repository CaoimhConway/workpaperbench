# Build status

Specification: v3.1. Started 2026-10-04 (America/Los_Angeles).

- Repository: https://github.com/CaoimhConway/workpaperbench; newly created private;
  verified API login `CaoimhConway` (ID 55163829), default branch `main`.
- Development software built for wp01/wp02/wp05. Local install/demo and 51
  lightweight reference, alternative, negative and boundary checks pass. Native
  Harbor integration and paid trials are still unrun.
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

Stage 1 local implementation: complete. Native integration/pilot: pending. Stage 2 expansion/freeze: pending.
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
