# Fresh answer replay

Fresh replay reruns the native Harbor oracle and separate verifier on GitHub Actions `ubuntu-24.04`. It makes no model call and does not read a saved regrade result. The verifier uses the task's existing trusted grader and replays only the submitted bounded SQL against pristine and changed SQLite copies. Run it through the workflow dispatch commands below. Direct local execution exits by design.

For a retained historical submission, select one slot or all eligible retained slots:

```sh
gh workflow run ci.yml --repo OWNER/workpaperbench --ref main --json <<'JSON'
{"integration":false,"fresh_replay":true,"dataset":"historical","replay_slot":"final-wp03-A-1"}
JSON
```

For all retained answers in the new dataset, set `dataset` to `real-v1` and `replay_slot` to `all`.

For an engineer-authored answer, commit one `answer.json` below `submissions/` and select its task explicitly:

```sh
gh workflow run ci.yml --repo OWNER/workpaperbench --ref main --json <<'JSON'
{"integration":false,"fresh_replay":true,"dataset":"real-v1","answer_path":"submissions/real-v1-wp02.json","task":"wp02"}
JSON
```

Replace `OWNER` with the public fork owner. The dispatcher needs Actions write access to that repository or fork. The job needs no secrets or contents write permission. The workflow inputs are `fresh_replay`, `dataset`, `replay_slot`, `answer_path`, and `task`. Use `answer_path` and `task` together for a committed file.

On a public fork, enable Actions and dispatch the workflow from that fork after committing the answer under `submissions/`. The answer must be a regular file no larger than 64 KiB, contain the task's exact `task_id`, and have no symlink in its path. The job rejects secret-bearing environments.

Each run writes a create-only receipt under `reports/fresh-replay/<run>-<attempt>/<dataset>/<slot>/receipt.json`. It records the input, dataset, task, current scorer, and task grader hashes, the prior verdict digest when available, the fresh verdict, and a comparison of completion and check states. A repeated write to the same run-attempt path fails instead of replacing the earlier receipt. Raw run output remains in the ignored `.raw/` directory.

## Research Challenge

All 72 retained challenge answers were freshly replayed in [37589616780](https://github.com/CaoimhConway/workpaperbench/actions/runs/37589616780), matching the complete original verdicts. This includes 18 development and 54 evaluation answers under their original scorers. The separate [corrected scoring run](https://github.com/CaoimhConway/workpaperbench/actions/runs/37589625073) passed 29 controls and graded all 54 unchanged evaluation answers under `challenge-1.1.3`. Original results remain preserved.

Use your authorized repository or enabled fork for all original challenge answers:

```sh
gh workflow run ci.yml --repo YOUR_LOGIN/workpaperbench --ref main -f integration=false -f fresh_replay=true -f dataset=challenge-v1 -f replay_slot=all
```

Replace `all` with `final-a03-inexpensive-1` for the saved Microsoft failure. For the consistent corrected evidence review, omit `fresh_replay` and `replay_slot`, and set `regrade=true`:

```sh
gh workflow run ci.yml --repo YOUR_LOGIN/workpaperbench --ref main -f integration=false -f regrade=true -f dataset=challenge-v1
```

A committed engineer submission can use `answer_path=submissions/reference-c02.json` and `task=c02` with that corrected-review command. Its diagnostics distinguish finance, evidence, recomputation and delivery. The current 1.1.3 review is bound to the original 54-slot manifest. Future model runs use new identities under the canonical original contract, as explained in [the challenge contract](CHALLENGE.md). Actual maintainer paths passed. A foreign-fork dispatch was not performed, the repository-selection and permissions guards are tested.
