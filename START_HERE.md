# WorkpaperBench — start here

**Build pack v3.3 · 4 October 2026.** This is a tool-neutral implementation handoff, not an implemented benchmark. It replaces earlier build packs. The v3.1 product specification and Actions execution contract are unchanged; do not merge older backlogs back in.

## Start

Extract this pack's contents, including `.github` and dotfiles, into the designated project folder. Open that folder in your coding agent with project file/terminal access, internet access, and permission to use your existing Git/GitHub authentication. **No local Docker, virtual machine, GPU, or model server is needed.** Heavy execution belongs on GitHub-hosted Ubuntu runners.

Use whichever coding environment you prefer. Your Claude and Codex subscriptions are available resources, not assigned roles or a requirement to use both. The same implementation stages and acceptance criteria apply in either environment. See `SETUP.md` for account and funding notes.

Paste this **one prompt**:

```text
Read AGENTS.md, SPEC.md, SETUP.md, and BUILD_PROMPTS.md. Build WorkpaperBench through all three stages now, in sequence, without asking for routine decisions or permission at stage boundaries. The standing project authorization in AGENTS.md is already granted. Execute and test; do not return another plan or expand the specification.

Use this device only for editing, Git/GitHub CLI, lightweight Python tests, and reviewing downloaded results. Run all Docker/Harbor integration and live agent trials through GitHub Actions. Reuse the existing SSH setup. Create/configure the dedicated repository, commit/push project files, set supplied project secrets, dispatch/watch workflows, fix failures, and finish the audited release as authorized. Inspect the actual account and repository before remote writes.

Use current primary documentation and installed code to choose compatible pins and one tool-capable hosted model. Observe development failures on wp01/wp02/wp05 before choosing one small intervention. The metric-migration case belongs in that pilot, not only in the final evaluation. Keep the eight-task ceiling. Do not stop for CEO feedback, human review, local Docker, task preferences, model approval, or separate spending approval within the recorded limits.

If authentication or a dedicated inference key is absent, write one exact unblock action in BUILD_STATUS.md, finish all independent work, and recheck before concluding. Never invent credentials, bypass tool-enforced permissions, fabricate results, or label an unrun gate passed. Resume from BUILD_STATUS.md rather than rebuilding completed stages. At the final stage, use a fresh read-only reviewer subagent when available, or a separate source-first review pass when not. The main agent owns fixes and verification.

End only after all achievable release gates are complete. Report the repo URL, actual checks/runs, generated findings, costs or explicit unknowns, and any genuine remaining blocker.
```

`BUILD_PROMPTS.md` contains the three stages for tools that need separate contexts. They are checkpoints, not three mandatory user approvals. After a context limit, use: **“Continue from BUILD_STATUS.md under the same standing authorization; complete the remaining stages.”**

## The only user-only prerequisites

1. **GitHub API authentication, if absent.** SSH already handles Git. Repository creation, Actions dispatch, and secret management also need authenticated `gh` or equivalent existing API access. The agent installs `gh` when missing. Browser/device login and account MFA may require you once; see `SETUP.md`.
2. **One funded, project-dedicated inference key.** Default: OpenRouter, with a non-resetting lifetime credit cap of USD 50 or less and no BYOK route. Supply it as the repository secret `OPENROUTER_API_KEY`, or privately through the agent's environment/ignored secret file so the agent can set it. Never paste it into chat. No model approval step is needed.

Existing coding subscriptions are not assumed to supply the separate benchmark API credit. No additional coding client, cross-tool invocation, or second subscription login is a build prerequisite. These instructions cannot grant an app permissions its own sandbox withholds. Use its normal project-scoped full-access mode where available; do not disable account-wide protections.

## What is supplied

- `SPEC.md`: authoritative scope, task briefs, grading invariants, experiment and finish line.
- `AGENTS.md`: shared standing authority, scope limits, and tool-neutral working rules.
- `CLAUDE.md`: a one-line import of the shared rules, not tool-specific implementation instructions.
- `BUILD_PROMPTS.md`: three implementation stages, automatically sequential.
- `SETUP.md`: agent-owned GitHub/bootstrap, single credential, exact login/secret paths.
- `build-notes/ACTIONS.md`: the two-workflow execution contract; avoids local containers.
- `build-notes/SOURCES.md`: checked primary references and source-acquisition boundaries.
- `.github/workflows/ci.yml`: executable, key-free cloud/Docker preflight; the builder expands this into actual CI.
- `.gitignore`, `.env.example`: safe initial file handling. No secret is included.

The starter preflight tests runner plumbing only, not Harbor isolation or financial correctness. Those checks must be implemented and actually run. `PACK_REVIEW.md` records what was checked while preparing this handoff.
