# Task authoring

The active suite is `datasets/real-v1`, with dataset-scoped task IDs and separate manifests. Keep published historical task identities and source bytes unchanged. A new snapshot is a separate directory and reviewed manifest, not a refresh in place.

Rebuild and verify the retained real-v1 packages offline:

```sh
.venv/bin/python scripts/build_real_tasks.py --check
```

Source-derived definitions are in `scripts/real_definitions.py`. Native packages use the same bounded JSON/SQL contract and unchanged scorer. Review independently calculated reference values, relevant evidence alternatives, positive and negative conclusions, source permissions and synthetic changed-input controls before freezing. Add no provider framework or arbitrary-code runner.

For a bounded engineer answer to an existing task, use the [fresh replay path](REPLAY.md). The local structure checker is safe, but submitted SQL must run only on Actions. A frozen dataset rejects reconstruction differences, and new acquisition output must use a distinct empty capture directory.

The original authoring guide follows for historical package layout.

# Author one native task

Extend a future version of the suite in a new branch. The published eight-task experiment remains immutable. A changed task requires new source review, controls and freeze before scored exposure. Adding more examples does not retroactively change the released comparison.

Use [wp03](../tasks/wp03/) as a compact example:

| File | Responsibility |
|---|---|
| `sources/wp03.json` | Authored tables, evidence, requested claims, references and changed-input values |
| `tasks/wp03/instruction.md` | Candidate request, units, cutoff and output location |
| `tasks/wp03/environment/` | Candidate-only database, excerpts, evidence and schema |
| `tasks/wp03/task.toml` | Native Harbor environment and time/resource limits |
| `tasks/wp03/solution/solve.sh` | Authored reference used by Harbor's oracle control |
| `tasks/wp03/tests/` | Separate pristine inputs, gold, verifier and changed-input fixture |

1. Edit the source JSON. Identify the origin, source group, periods, units and evidence locators. Mark synthetic numbers and labels explicitly. Limit the work to a few requested values and at most one bounded conclusion.
2. Independently calculate the reference values from the source. Include a legitimate alternative query and a plausible wrong query. Choose a changed-input fixture that exposes that error while preserving the metric's definition and coverage.
3. Run `python scripts/build_tasks.py` in the future-suite branch to generate packages. This rebuilds databases and candidate files, so it must never be used to synchronize grader fixes into the frozen experiment.
4. Run the lightweight suite and the full native Actions controls. The native oracle reads the authored solution, the candidate sees only environment files, and the separate verifier replays SQL against its own pristine inputs.
5. Review candidate requests without consulting the reference answer. Freeze the new version only after source, licensing, isolation, safe alternatives and wrong-answer controls pass.

For a key-free native reference check in a GitHub-hosted Ubuntu 24.04 workflow, use the same pinned installation steps as [ci.yml](../.github/workflows/ci.yml), then:

```sh
harbor trial start -p tasks/wp03 -a oracle --trial-name wp03-reference --trials-dir .raw/reference
```

The canonical full-suite command is the README's tested Actions dispatch. Keep candidate instructions/schema, databases, evidence and treatment unchanged when correcting only a verifier. Copy the two trusted grading modules into all eight `tests/workpaperbench` directories and register their reviewed hashes separately.
