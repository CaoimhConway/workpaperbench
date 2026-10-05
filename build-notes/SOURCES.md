# Checked primary references and research boundaries

Initial review and targeted v3.1 recheck: **4 October 2026**. These establish documented capabilities and source material, not successful execution of this unbuilt project. The implementation must verify its exact pins and runner. Do not import speculative prior-research benchmark claims into the README.

| Key | Primary source | How it informs this pack |
|---|---|---|
| R1 | Artemis, Stablecoin Metrics Methodology — July 2026: https://www.artemis.ai/docs/data-reference/stablecoin-methodology | Describes gross versus prior adjusted transfers, unchanged API field names and a separately updated Snowflake surface. Motivation, not an allegation of agent/product failure or proof of historical break. |
| R2 | Tesla Q2 2024 10-Q: https://www.sec.gov/Archives/edgar/data/1318605/000162828024032662/tsla-20240630.htm | Period/units/quarterly R&D source. Recheck context; do not trust extracted scalar alone. |
| R3 | Apple quarter ended 2024-03-30 10-Q: https://www.sec.gov/Archives/edgar/data/320193/000032019324000069/aapl-20240330.htm | Services revenue/profit and fiscal periods. |
| R4 | Circle USDC addresses: https://developers.circle.com/stablecoins/usdc-contract-addresses ; Circle implementation: https://github.com/circlefin/stablecoin-evm | Authentic contract identity; validate ABI/decimals/event semantics for the chosen capture. |
| R5 | Ethereum JSON-RPC: https://ethereum.org/en/developers/docs/apis/json-rpc/ ; ERC-20: https://eips.ethereum.org/EIPS/eip-20 | Logs, block identities and transfer interface; no assumption that every token's mint/burn behavior is identical. |
| R6 | PublicNode Ethereum service: https://ethereum.publicnode.com/ | Lists `https://ethereum-rpc.publicnode.com` as the public endpoint. Availability/history/rate limits still require an actual request. |
| R7 | Harbor integrated agents: https://docs.harborframework.com/agents/pre-integrated-agents ; implementation: https://github.com/harbor-framework/harbor/blob/main/src/harbor/agents/installed/hermes.py | Native Hermes integration, skill/tool options, model/provider routing and substantial cold setup. Inspect installed revision. |
| R8 | GitHub runners: https://docs.github.com/en/actions/reference/runners/github-hosted-runners ; billing: https://docs.github.com/en/billing/concepts/product-billing/github-actions ; limits: https://docs.github.com/en/actions/reference/limits | Full Ubuntu VM versus slim; public/private quota differences; hosted-job timeout. Not a guarantee of zero private-run cost. |
| R9 | Official Ubuntu 24.04 runner inventory: https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md | Lists Docker/Compose and system tools; check actual runner resources/versions. |
| R10 | Harbor separate verifier: https://docs.harborframework.com/tasks/separate-verifier ; network policies: https://docs.harborframework.com/tasks/network-policies | Default verification is shared. Separate mode/transfer is explicit; Docker allowlist support has Linux/nftables requirements. |
| R11 | GitHub workflow dispatch: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow | Default-branch requirement and CLI dispatch/watch. “Manual dispatch” can be performed by the authorized agent. |
| R12 | OpenRouter key metadata/limits: https://openrouter.ai/docs/api_reference/limits ; catalogue: https://openrouter.ai/api/v1/models | Limit/reset/remaining/usage checks and endpoint tool support. A dedicated non-resetting provider cap survives fresh runners; local environment flags do not enforce it. |
| R13 | GitHub secure use: https://docs.github.com/en/actions/reference/security/secure-use | Least-privilege tokens, untrusted workflow input and redaction caveats. Raw artifacts are not automatically safe. |
| R14 | gh auth: https://cli.github.com/manual/gh_auth_login ; repository creation: https://cli.github.com/manual/gh_repo_create | Existing SSH can be reused; API/CLI authentication is separate. |
| R15 | GitHub Actions secrets: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets | Repository secret creation, CLI and stdin/file ingestion. |
| R16 | SQLite security: https://www.sqlite.org/security.html ; authorizer: https://www.sqlite.org/c3ref/set_authorizer.html ; Python API: https://docs.python.org/3/library/sqlite3.html | Layered query restrictions and bounds rather than string-prefix “validation.” |

Related implementation precedent: https://github.com/NousResearch/hermes-toolperf-evals and https://developer.nvidia.com/blog/tracing-agent-harness-behavior-with-nvidia-nemo-relay/ . Their relevance is connecting a reproducible case to an observed failure and a controlled change. Do not claim to invent tracing or a new evaluation category.

Additional references for the final pre-build review:

| Key | Primary source | How it informs this patch |
|---|---|---|
| R17 | Anthropic, Demystifying evals for AI agents: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | Clear task requirements, balanced cases, output-focused grading, transcript inspection and honest saturation reporting. Not evidence that WorkpaperBench itself is valid. |
| R18 | Nous, Machine Learning Engineer, Evals: https://nousresearch.com/careers/machine-learning-engineer-evals | Current explicit demand for benchmark extensions, graders, failure analysis and reproducible engineering. Role fit, not a hiring guarantee. |
| R19 | Artemis product homepage: https://about.artemis.ai/ | Current financial-research and dataset-reconciliation workflows. Does not disclose internal hiring priorities or prove any production failure. |

## Source review boundary in this handoff

The financial-document URLs, Artemis methodology, Circle address documentation, GitHub runner/secret/dispatch documentation, Harbor behavior and provider catalogue/limits were inspected during preparation. No observed USDC log corpus was obtained here: the attempted RPC request from the preparation container failed at DNS resolution. That does not establish the endpoint is down; retry within the bounded acquisition policy on the real Actions runner. Do not label the attempted request as a successful capture.

The exact Harbor/Hermes version pair, effective network isolation, provider/model runtime and GitHub account state have not been exercised. They are stage-1 checks. No live result, prototype measurement, repository creation or remote Actions run is bundled in this pack.

For v3.1, R1, the R7 upstream Hermes adapter, separate-verifier documentation, the ToolPerf repository, and R17–R19 were re-opened. R7 explicitly forwards the inference key into the installed agent environment; v3.1 removes the contradictory blanket “no key in candidate” stage gate without allowing gold/GitHub secrets/host access. Previously recorded source and runtime limitations remain. No cloud runtime, new source capture or model trial was executed for this patch.

## Retained subscription-setup references (recorded in v3.2)

These setup references were recorded in v3.2 and retained without a new web review in v3.3. They concern authentication, billing boundaries, and shared instruction loading, not implementation assignments. No user account, subscription tier/quota or native CLI login was inspected.

| Key | Primary source | Supported point |
|---|---|---|
| B1 | https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan | Claude Code subscription sign-in, shared usage limits and separately billed API fallback. Exact owner tier is unknown. |
| B2 | https://code.claude.com/docs/en/authentication ; https://support.claude.com/en/articles/9876003-i-have-a-paid-claude-subscription-pro-max-team-or-enterprise-plans-why-do-i-have-to-pay-separately-to-use-the-claude-api-and-console | Native sign-in/status and credential precedence. Subscription access is not general API credit; inspect the active route, not just key presence. |
| B3 | https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan ; https://developers.openai.com/codex/auth/ | Codex subscription versus API authentication, login/status and actual plan limits. The developer URL redirected to https://learn.chatgpt.com/docs/auth during review. |
| B5 | https://code.claude.com/docs/en/memory | A one-line @AGENTS.md import keeps Claude and Codex instructions shared; direct AGENTS.md support varies with version and other instruction files. |

No product-specific builder/reviewer assignment or cross-tool orchestration is part of this handoff. The project's existing audit requirements remain tool-neutral.
