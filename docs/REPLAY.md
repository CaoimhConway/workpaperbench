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
