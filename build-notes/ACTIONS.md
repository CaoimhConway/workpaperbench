# GitHub Actions execution contract

This is execution detail for the same small project, not a third architecture. The supplied `ci.yml` is a runnable **Docker plumbing preflight only**. Expand it in stage 1; add one `benchmark.yml`. Do not ship a green scaffold as completed CI.

## Runner and jobs

Use `runs-on: ubuntu-24.04` full VM. GitHub documents standard Linux VMs for both private/public repositories, while `ubuntu-slim` is a different restricted environment [R8]. Docker/Compose are listed on the Ubuntu image [R9]. Verify actual `docker version`, `docker compose version`, memory/disk, image digest and native Harbor behavior; documentation is not an integration test.

No job-level `container:` wrapping the runner; Harbor drives Docker from the VM host. No Docker-in-Docker service, self-hosted runner, local `act`, GPU, GHCR registry or persistent VM. Use minimal images and serial execution. A standard runner is the first choice, not a claim that arbitrary large images fit. If space fails, reduce project images/cache and clean project-owned ephemeral images; do not pay for larger runners automatically.

**Do not put 48 trials in one long job.** Native Hermes setup can be substantial per fresh container [R7]. Begin with one slot per job, or one A/B pair per job only when the measured cold setup plus solving/cleanup fit comfortably. Use a native matrix from the committed schedule, `max-parallel: 1`, `fail-fast: false`, explicit job timeout (start at 35 minutes per single slot), and a constant live-workflow concurrency group with `cancel-in-progress: false`. No general sharding system. A supported immutable install cache may be used after measurement; do not snapshot sessions or build a cache service. Run-time limits never include cold installation by accident.

## ci.yml — no paid secrets

Triggers after implementation: `push`/`pull_request` for lightweight unit/schema/grader/manifest/demo tests; `workflow_dispatch` and a suitable protected main-push job for container integration. Keep expensive checks out of a per-file matrix. Do not use `pull_request_target`.

Required real container controls: native oracle/reference passes; empty submission fails; candidate cannot reach gold; submitted artifacts cannot overwrite trusted tests/data; verifier sees pristine data/no inference key; network policy behaves as declared; constrained SQL stops/denies forbidden operations; fresh runs do not share learned state. No API key is needed for these controls.

Use native Harbor `environment_mode = "separate"` and phase-specific network policy. Setup may download dependencies. Scored agent phase allows the inference endpoint only, verifier has no network. Docker allowlists require relevant Linux/nftables support [R10]. Verify on Actions; fix pins/configuration, not by making the agent unrestricted. The trusted runner alone uses GitHub to fetch/upload. Never pass its token or Docker socket to candidate containers.

## benchmark.yml — dispatched by the coding agent, not a user clicking each run

Only `workflow_dispatch`, default branch, exact committed manifest. The coding agent calls `gh workflow run`, watches `gh run watch`, downloads artifacts, corrects true defects and continues. The workflow file must first be on the default branch for dispatch [R11]. Do not add environment reviewers or another approval flag. `workflow_dispatch` is the technical trigger, not a new spending-consent request.

Two workflow modes are enough: `pilot` (declared development slots) and `final` (frozen full schedule). Validate bounded input enums/manifest ID; no arbitrary commands, external checkout URL or unreviewed ref input. For secret-bearing runs require the repository's default branch and expected owner/repo. A fresh unaudited fork does not inherit autonomous dispatch authority.

Permissions: `contents: read`; add `actions: read` only when needed to reconcile past artifacts/status. Use checkout with `persist-credentials: false`; pin actions to verified full commit SHAs during implementation. No repository PAT/SSH key/admin token in Actions. The local agent does commits/pushes; workflow jobs do not need repository write access.

Expose `OPENROUTER_API_KEY` only to the trusted budget-check/live-execution step. Do not put it in workflow-wide `env`, Docker build arguments/layers, verifier, test job, command arguments or artifacts. Only that dedicated inference credential enters the candidate's required agent environment. The current installed Hermes adapter forwards it as an environment variable; do not promise it is inaccessible to terminal code in the same environment. Keep the provider cap and endpoint-only egress as the limited backstops, and explicitly verify that the separate verifier/replay sees no key. No new proxy or adapter. Unset unrelated provider keys. No `set -x`, blanket environment dumps or raw job/config dumps.

Use a single dedicated key with `0 < limit <= 50`, `limit_reset == null`, enough `limit_remaining`, no external BYOK credentials, and no shared unrelated usage. Check the provider endpoint before live calls; a new VM must not reset the allowance [R12]. Invalid/missing key metadata blocks paid execution, not offline work. The coding agent may configure a supplied dedicated key's cap through already authorized provider access; it may not silently repurpose a general key or mint admin credentials.

After a short pilot, check that the planned final campaign fits remaining inference credit and Actions allowance. Limits and counts constrain spending; do not call a local estimate a guaranteed hard GitHub billing cap. Use the account's existing enforceable budget if available; do not alter unrelated budgets. Under AGENTS.md, incidental standard-runner charges up to the stated project ceiling are already authorized. Record project run durations/storage and current rates. Stop dispatching work when the ceiling/quota is exhausted rather than buy capacity or use this device for Docker.

## Records, failure handling and restart

Before dispatch, commit the frozen schedule with unique slot IDs `(campaign, task, arm, repetition)`. Persist Actions run ID/attempt and commit SHA in `BUILD_STATUS.md` or the ordinary report record. Never use an Actions rerun as a clean reset of spending or a failed scored attempt.

Each slot writes start metadata, submitted output if present, verdict/error, available usage and finish status. Runner error without output is still a recorded slot. Finish/postprocess steps use `if: always()` where possible, but hard timeouts/cancellation can prevent upload: reconcile against GitHub status and mark the slot lost/infra-failed. Never infer a missing artifact means “not attempted.”

Use native upload/download-artifact actions with unique names including commit/campaign/run/attempt/slot. `retention-days: 7`; no artifact or dependency cache of raw secrets/home directories/images. Do not upload whole Harbor job directories. Produce an allowlisted, secret-scanned bundle (answer, verdict, sanitized tool events, minimal config/version/cost metadata). Raw traces stay ephemeral unless independently scrubbed. Disable Actions workflow-command interpretation while capturing untrusted agent output, and do not stream raw model text into runner command channels.

GitHub masking is not an artifact redactor [R13]. Exact-key redaction alone is not sufficient; do not record credentials in the first place. Sanitize locally on the runner before upload. Public-repo artifacts/logs must be treated as public. The local coding agent downloads the small evidence bundles, preserves canonical sanitized records under `reports/runs/` or a release asset, and regenerates results BEFORE artifacts expire. No S3/database/checkpoint service.

On restart, retrieve existing run/artifact state through `gh`, match the frozen schedule, and dispatch only truly unstarted slots. Completed bad answers are not rerun. Uncertain lost slots remain failed/unknown; a diagnostic rerun gets a supplemental ID. Budget comes from provider lifetime usage, not downloaded artifacts. Repository run history is the control-plane record, not candidate statements.

Native concurrency plus a thin schedule loop are enough. Avoid building a durable orchestration platform for this experiment.

## Commands the builder must provide and actually test

- Lightweight local install/test/demo, no Docker or key.
- `gh workflow run ci.yml ...` and exact watched run ID for reference/isolation checks.
- Pilot and final `gh workflow run benchmark.yml ...` commands with no interactive input.
- `gh run download <id> ...` and local report generation from sanitized saved records.
- A resume sequence identifying missing slots without repeating scored trials.

Pinned dependency commands/Harbor flags depend on the compatible version discovered by the builder. Do not invent them now or install a moving `main` merely to copy an old example. This file specifies outcomes, not fake already-tested native flags.
