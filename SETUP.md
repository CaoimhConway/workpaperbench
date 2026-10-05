# WorkpaperBench — setup, owned by the agent

**Build setup v3.3: tool-neutral use of existing coding subscriptions; unchanged v3.1 product scope and Actions-only heavy execution.** Read AGENTS.md for standing authority. The user does not need to select a model, approve commits/pushes, start Docker, or click each Actions run.

## 0. Available subscriptions and funding boundaries

The owner already has Claude and Codex subscriptions. They are available development resources; there is no prescribed division of implementation or review work, required tool switch, cross-client invocation, or requirement to use both. Continue in the chosen coding environment. Do not install or authenticate another coding client merely to satisfy this pack.

Reuse an existing supported subscription login and check its actual entitlement and active billing route when necessary [B1–B3]. Do not assume a tier or unlimited quota, buy another coding plan, or silently fall back to separately billed coding APIs or extra usage. Preserve existing account settings; any genuinely necessary browser/MFA action remains a one-time external prerequisite, not an implementation decision.

The Hermes evaluation still uses the project's separate, capped inference credential. Do not export subscription tokens/auth caches into Hermes, GitHub Actions, task images, or release artifacts. Missing benchmark credit blocks only paid trials; it does not prevent independent build work. Preserve project state, frozen configurations, run IDs, and cumulative costs whenever a session changes.

`AGENTS.md` contains the shared project instructions. The optional compatibility file `CLAUDE.md` only imports `AGENTS.md` [B5]; it assigns no separate implementation behavior. Preserve existing user instructions when merging files. Do not duplicate the requirements by tool. Record actual review coverage and limitations without requiring a particular reviewer product.

## 1. Bootstrap

Inspect the designated folder, Git root/status/remotes, OS, existing tools and authenticated GitHub account. Reuse existing SSH. Install missing `gh`/`uv` with the existing package manager or official user-local path; do not change system Python or demand local Harbor/Docker. Local Python is for small tests/reporting. Finish independent implementation during any login delay.

Check the GitHub API login without displaying tokens:

```sh
gh auth status
gh api user --jq .login
```

For this personal project the expected account is `CaoimhConway`. Use it when confirmed; do not create a similarly named repository under an unrelated organization/account. If another account is active, reuse an already authenticated matching account via the normal CLI switch; otherwise record the mismatch as the precise external blocker.

If the user must log in once, the command is:

```sh
gh auth login --hostname github.com --git-protocol ssh --web --skip-ssh-key
```

SSH Git and CLI/API access are distinct. This command reuses the user's SSH setup rather than generating/uploading a new key [R14]. Browser/MFA and tool sandbox grants cannot be synthesized from a document. Do not request a new PAT by default or repeatedly restart login flows.

## 2. Create/reuse the repository autonomously

Initialize Git ONLY when the folder is not already the intended repo. Preserve changes/branch conventions. Use existing identity; otherwise derive repository-local name/noreply address from the authenticated profile. Never invent an identity or rewrite history.

Inspect `CaoimhConway/workpaperbench` and any current `origin`. Reuse a matching project. When absent, the agent is authorized to create it private:

```sh
gh repo create CaoimhConway/workpaperbench --private --source=. --remote=origin
```

Do not run this blindly over an existing remote. Review/stage project-owned files and secret exclusions, commit, then push the actual branch. Put the workflow on the repository's default branch before dispatch. Creating/pushing/configuring this dedicated project is already authorized; no separate confirmation.

Run the supplied no-secret cloud preflight immediately when remote access works:

```sh
gh workflow run ci.yml --repo CaoimhConway/workpaperbench --ref main
gh run list --repo CaoimhConway/workpaperbench --workflow ci.yml --limit 5
# Select the new run matching the pushed commit, then:
gh run watch RUN_ID --repo CaoimhConway/workpaperbench --exit-status
```

`main` is an example for a new repo; use the actual default branch. Match commit/run metadata rather than blindly watching another user's latest job. This preflight proves only runner plumbing. Stage 1 must add/run actual Harbor verifier tests.

## 3. One inference credential, no local execution setup

Default provider is OpenRouter. The user supplies a dedicated, funded key named for this project with a **non-resetting credit cap ≤ USD 50** and no external BYOK route. The agent verifies current metadata and picks one compatible tool-capable model before freeze. Do not force a Nous model just because the agent framework is Hermes. No extra host Hermes login, portal subscription, Hugging Face token, RPC key or paid financial-data account is required for the default path.

Preferred: user enters the key once as the repository Actions secret `OPENROUTER_API_KEY`, or with the CLI in their own terminal:

```sh
gh secret set OPENROUTER_API_KEY --repo CaoimhConway/workpaperbench
```

No value appears in this command. Alternatively, the user can provide the key in the coding agent's environment or `.secrets/openrouter.key` (ignored, mode 600). The agent may transfer an explicitly supplied key without a new permission prompt. For an existing secret file, shell redirection does not put the value into an argument:

```sh
gh secret set OPENROUTER_API_KEY --repo CaoimhConway/workpaperbench < .secrets/openrouter.key
```

Do not print/read the key into chat, echo it, commit it, pass it via `--body` arguments, or search unrelated credential stores. A secret already on GitHub need not be recovered locally; test its presence and cap inside the trusted remote step. `gh secret list` reveals names, not values. GitHub secret management and stdin/file paths are documented [R15].

The optional `.env.example` is only a private local transport convenience. There is no disabled-live flag or zero-budget approval gate to wait for. The user's standing permission and explicit workflow dispatch authorize live work inside the stated ceilings. The runner must still verify a valid limited key; text in a spec does not enforce provider spending.

A new key with no prepaid balance cannot make paid calls. Account registration, MFA or an unavailable payment source can require the user's one-time action. Record it once; do not create a new account, enable recurring billing or buy unapproved subscriptions. Authorized inference uses supplied funded credit.

## 4. Small remote machine defaults

Use standard full Ubuntu GitHub-hosted VMs, not `ubuntu-slim`. Perform all Docker/Harbor installation and execution there. Hosted inference means no model weights or GPU. Start with serial trials and minimal task images. CI has no inference secret; only an explicit benchmark dispatch does. See `build-notes/ACTIONS.md` for frozen scheduling, setup limits, secret boundaries and preserved artifacts.

Private standard-runner minutes/storage consume the account's allowance, then can be billed; public standard runners have free compute subject to GitHub's applicable policies. Larger runners are not the default and can be billed regardless [R8]. Do not promise that every private run costs zero. Use the authorized USD 10 incremental Actions ceiling, minimal short-retention artifacts, and existing quotas. Publish the audited software-complete dedicated project as allowed, not private data to save fees.

## 5. Publication and files

Install/merge `.gitignore` before storing credentials. Check both working files and Git history, not just the final diff. Exclude raw traces, caches, secret files, private correspondence/resume/client data and the full host home directory from uploads/images. Nothing in this build requires publishing the user's hiring conversations.

After software/source/secret review, the agent may make the newly created dedicated project public and tag an accurately labeled software prerelease. It may publish the measured release after the full experiment. Do not publish empirical claims early. Existing unrelated repository visibility is untouched. Confirm all checks mechanically, not by asking the user to sign off.

For SEC acquisition, use a descriptive user agent such as `WorkpaperBench/0.1 (research; caoimh@summitlabs.xyz)`, cache responses and respect the current SEC access/rate guidance. This is the owner's already supplied public business contact, not an API credential. If a public source denies access, use an authentic issuer mirror or the documented fallback; do not bypass an access control.

No cloud VM, website, domain, PyPI package, container registry, paid data service, CEO outreach or human-review panel is a prerequisite.

## 6. Blockers without stalling

| Missing thing | Continue | Record as blocked |
|---|---|---|
| GitHub API login/permission | Code, sources reachable locally, lightweight tests, workflow implementation | Repo creation/Actions dispatch/integration proof |
| Dedicated funded capped model key | Entire software/reference/integration build | Exploratory/final paid runs |
| Public log capture | Use the explicit synthetic downgrade and label it | Claim that the ledger case uses observed activity |
| Hosted runner restriction | Debug compatible pins/config on Actions; finish independent tasks | Isolation/live-run gate, never quietly run on local host |
| Human feedback or CEO input | Everything | Nothing; don't claim external validation |
| Budget exhausted | Report/account for existing work, finish offline/review work | Unrun paid slots; don't fake full evaluation |

Keep exact commands and real results in one BUILD_STATUS.md. Recheck resolved prerequisites before ending. Otherwise finish with the achieved state and a single concrete unblock action; do not loop on approvals or regenerate the plan.
