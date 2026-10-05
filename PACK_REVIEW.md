# WorkpaperBench v3.3 — tool-neutral handoff correction

**Reviewed:** 4 October 2026. **Status:** document-only correction; no implementation or live experiment executed here.

## What changed

Removed the v3.2 Claude/Codex implementation-role assignments, cross-client invocation examples, second-client setup requirements, tool-specific handoff policy, and model-selection advice for the coding clients. The three build stages and their audit requirements are generic again. Either coding environment can complete the project; using both is not required.

Existing subscriptions are retained only as available resources and setup/billing context. There is no new development purchase or automatic API-billed fallback. The single `AGENTS.md` remains authoritative; `CLAUDE.md` only imports it. Local client-state ignore rules remain for privacy.

## What did not change

`SPEC.md`, `build-notes/ACTIONS.md`, `.github/workflows/ci.yml`, `.env.example`, `.gitignore`, and `CLAUDE.md` are byte-for-byte identical to v3.2. The headline, eight tasks, development/evaluation split, grading rules, 48 final trials, exploratory limits, paid budgets, standing authorization, and Actions-only heavy execution have not changed.

## Validation scope

`PACK_VALIDATION.json` records the checks performed for this revision: unchanged-file comparisons, absence of tool-specific implementation assignments and invocation commands, generic three-stage structure, source-key references, Markdown code fences, supplied JSON and workflow YAML parsing, shell-example syntax, and ZIP content integrity. These are handoff checks, not a tested application, runtime, subscription login, remote workflow, or model experiment.

The setup sources were carried forward, not newly researched. No GitHub account or subscription was accessed and no benchmark or coding-client session was run. Start with the single prompt in `START_HERE.md`; do not add another planning stage.
