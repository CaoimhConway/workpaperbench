# WorkpaperBench — agent authority and working rules

## Project writing rules

- Never use semicolons unless absolutely necessary.
- Use `-` instead of an em dash in project text.
- Never state or imply that this project was created by AI. Do not add AI
  co-authorship, co-author trailers, signatures or generation notices to code,
  documentation, commits or other project artifacts.

The user has authorized autonomous completion of this project. `SPEC.md` v3.1 is the sole product authority; `SETUP.md` and `build-notes/ACTIONS.md` define execution. Follow the three stages in `BUILD_PROMPTS.md` continuously. Do not ask for routine permission or present a new plan instead of implementing.

## Tool-neutral implementation

Use the coding environment in which this project is opened. No tool is assigned a specific implementation or review role, and using multiple coding clients is not required. Tool choice does not change the scope, evidence requirements, authority, or finish line. Available subscriptions and funding boundaries are documented in `SETUP.md`; do not add a tool-orchestration layer or require another client to finish.

## Standing project authorization

Without further confirmation, you may:
- Inspect/edit/test project files; install necessary user-local/project dependencies and tools; use public primary sources; choose compatible dependency pins and one hosted tool-capable model.
- Initialize this designated Git repository, use the existing SSH setup/identity, create a dedicated private `workpaperbench` repository under the confirmed personal account `CaoimhConway`, add a verified remote, commit/push project-owned changes, and create normal branches/tags/releases. Reuse an existing matching project rather than overwrite it.
- Configure this repository's Actions, variables and supplied project-specific secrets; dispatch/watch/cancel project workflows, download artifacts, fix failures and rerun justified engineering checks. Do not put approval environments in the critical path.
- Run paid inference using the supplied dedicated credential within **USD 50 cumulative provider credit**, including development and failed calls. Use standard GitHub-hosted Linux runners within included quota or **USD 10 incremental project Actions charges**. These are ceilings, not spending targets. No additional spending approval is needed inside them; do not raise/reset caps, buy subscriptions, or enable auto-top-ups.
- Publish the NEW dedicated project after the source/license/secret/history audit and software-complete gate, then publish the measured release after its separate empirical gate. A software-only prerelease must say it is not yet evaluated. Public visibility is allowed, not a reason to skip the audit. Preserve an existing user's repository visibility unless this is unambiguously the dedicated project authorized here.
- Select the specified source-acquisition fallbacks, correct genuine bugs, choose one development-grounded intervention, and simplify unnecessary code. Log consequential decisions briefly; do not request task/model/architecture preferences.

This authority does not extend to unrelated repositories/accounts, financial trades, client data, reading unrelated private material, deleting user work, force-pushing shared history, changing global SSH/Git settings, adding broad admin tokens, leaking secrets, disabling account safeguards, or contacting people/companies on the user's behalf. Draft an upstream contribution note when justified; external outreach is not a build dependency.

## Resource and account defaults

No local Docker/Podman/VM/act, local inference, GPU setup, self-hosted runner, or new cloud subscription. Local work is editing, small Python tests, Git/gh, and artifact inspection. All container builds, Harbor tests and paid trials run in Actions on `ubuntu-24.04` full VMs, not `ubuntu-slim` or macOS. One live trial at a time. Preserve the provider-side lifetime cap across every job/session.

Authenticate with the existing account. If Git identity is missing, derive a repository-local identity from the verified GitHub profile/noreply address; do not invent one or modify global config. Never replace unrelated remotes or initialize inside a parent repo accidentally.

A missing login, credential, policy grant or exhausted balance is an external blocker, not a request for a preference. State its exact unblock action once in `BUILD_STATUS.md`, complete independent work and recheck later. Do not repeatedly ask or falsely claim completion. Do not create substitute accounts or harvest credentials. Read only the explicitly supplied project key for secure transfer; never print it.

## Scope and evidence

Eight tasks: development wp01/wp02/wp05 and evaluation-not-tuned wp03/wp04/wp06/wp07/wp08; one JSON/SQL workpaper; at most one bounded conclusion per task; deterministic grading; one small intervention; one model; 48 final slots; at most 12 exploratory live slots. No dashboard, platform, service, generic scraper/indexer, billing backend, plugin system, arbitrary-Python replay, or extra benchmark/model. Three or four ordinary runtime modules are preferable to class hierarchies. Review runtime growth around 1,500 hand-written lines, excluding tests/assets/config; never minify to meet a number.

Source-backed motivation is not observed product failure. Separate real captures, synthetic fixtures, authored reference outputs and actual model submissions. No fabricated history, citations, costs, human review, tool results or performance claims. An unhelpful intervention and a ceiling result must remain visible.

## Test and security boundaries

Use native Harbor/Hermes and native separate verification. Test this on the actual hosted runner, including network policy and fresh state. Never run candidate-written code on the host. Only constrained SQL is replayed against pristine data. Gold, the checkout, Git history, GitHub credentials and Docker sockets do not enter the candidate container. Only the dedicated capped inference key reaches the required agent environment; native installed execution is NOT a guarantee that its terminal tools cannot read that key. Document the actual behavior. The separate verifier/replay has no inference key/network. Do not build an inference proxy or custom adapter to promise stronger isolation. No paid secrets on PR/push CI or `pull_request_target` workflows.

Review staged files, candidate image contexts, logs, artifacts and Git history for secrets and private data before publishing. GitHub log masking is not proof of safe artifact contents. Keep raw traces local/ephemeral until sanitized. If a secret is exposed, cancel affected runs, remove public exposure where authorized and record the required rotation. Do not claim deleting a file revokes a key.

## Working style

Inspect before editing, preserve existing user changes, implement the smallest correct thing, and test commands before recommending them. Read primary sources and independently calculate reference values instead of trusting earlier notes. Review valid alternatives as well as wrong submissions. Fix defects rather than weaken the grader to improve scores.

Keep one concise `BUILD_STATUS.md` with versions, Git/Actions run IDs, commands/results, spend accounting, freeze hashes, decisions and blockers. Do not generate more planning documents. Use a fresh read-only audit context when available; do not launch a swarm editing shared interfaces. Finish each achievable gate and advance without waiting for a user message.
