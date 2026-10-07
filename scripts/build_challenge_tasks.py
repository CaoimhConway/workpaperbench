"""Reconstruct challenge task packages from retained factual dossiers, offline."""
import argparse
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from build_tasks import database, write_json
from build_real_tasks import sqlite_contents

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets/challenge-v1"

LEGACY_TOLERANCE_INSTRUCTION = (
    "All numeric tolerances are 0.000001 in the requested unit, applied to the displayed source precision."
)

COMMON = """

Task identifier: {task_id}.
Inputs are in /workspace: data.sqlite, evidence.json, sources.md, schema.json and check_answer.py.
Write one workpaper to /logs/artifacts/answer.json, following schema.json. Use exactly the requested claim IDs and units.
For each answered claim, supply a finite number and deterministic read-only SQLite returning one row and one numeric column. Any column alias is accepted.
Calculations must recompute on pristine original inputs and synthetic schema-compatible controls. Controls can change observations, reorder rows and change irrelevant periods. No hidden control values are supplied. Conclusions are scored on the original dossier only.
Cite the stable section IDs supporting each claim, including required definitions and period or population context. Equivalent source paths are accepted. Shared context_evidence may hold common definitions, while each claim must cite its own supporting facts. Do not cite unrelated sections.
Use insufficient_evidence with null value and null SQL for an unavailable requested quantity. Conclusion verdicts mean supported, contradicted, or not_established. Only the requested proposition is scored. Do not add factual prose outside the structured fields. Reason codes are optional and are not scored.
All numeric tolerances are 0.000001 in the requested unit, applied to the displayed source precision. Use the public structure checker: python /workspace/check_answer.py /logs/artifacts/answer.json. It checks delivery only and contains no financial answers. No live source acquisition is needed.
"""

COMMON_110 = COMMON.replace(
    LEGACY_TOLERANCE_INSTRUCTION + " Use the public structure checker:",
    "Per-claim absolute numerical tolerances in requested units:\n{claim_tolerances}\nUse the public structure checker:",
)

UNIT_NORMALIZATION_110 = (
    "\n\nFor unit matching, the grader trims surrounding whitespace, ignores case, and treats runs of ordinary whitespace or underscores as a single underscore. It does not convert units or scales.\n"
)


def claim_tolerance_lines(definition):
    lines = []
    for claim in definition["reference"]["answers"]:
        expected = definition["gold"]["answers"][claim["id"]]
        tolerance = format(Decimal(str(expected["tolerance"])), "f")
        lines.append(f"- {claim['id']}: {expected['unit']} - {tolerance}")
    return "\n".join(lines)


def package(definition, destination):
    task_id = definition["task_id"]
    scorer_version = definition.get("scorer_version", "challenge-1.0.0")
    if scorer_version not in ("challenge-1.0.0", "challenge-1.1.0"):
        raise ValueError("unsupported_challenge_scorer:" + str(scorer_version))
    key = task_id.removeprefix("challenge-v1-")
    task = destination / "tasks" / key
    environment, tests, solution = [task / name for name in ("environment", "tests", "solution")]
    for directory in (environment, tests, solution):
        directory.mkdir(parents=True)
    database(environment / "data.sqlite", definition["tables"])
    shutil.copyfile(environment / "data.sqlite", tests / "data.sqlite")
    schema_source = (ROOT / "config/schemas/challenge-1.1.0.json" if scorer_version == "challenge-1.1.0"
                     else DATASET / "schema.json")
    for directory in (environment, tests):
        shutil.copyfile(schema_source, directory / "schema.json")
        write_json(directory / "evidence.json", definition["evidence"])
        (directory / "sources.md").write_text(definition["context"].rstrip() + "\n")
    shutil.copyfile(ROOT / "scripts/check_answer.py", environment / "check_answer.py")
    verifier = (ROOT / "scripts/verify.py").read_text().replace("from workpaperbench.grading import grade", "from workpaperbench.challenge_grading import grade")
    (tests / "verify.py").write_text(verifier)
    modules = tests / "workpaperbench"
    modules.mkdir()
    for name in ("__init__.py", "grading.py", "challenge_sql_worker.py"):
        shutil.copyfile(ROOT / "workpaperbench" / name, modules / name)
    scorer_source = (ROOT / "config/scorers/challenge-1.1.0.py" if scorer_version == "challenge-1.1.0"
                     else ROOT / "workpaperbench/challenge_grading.py")
    shutil.copyfile(scorer_source, modules / "challenge_grading.py")
    gold = copy.deepcopy(definition["gold"])
    gold["task_id"] = task_id
    if scorer_version == "challenge-1.1.0":
        gold["scorer_version"] = scorer_version
    gold["controls"] = []
    for index, control in enumerate(definition["controls"]):
        name = f"control-{index + 1}.sqlite"
        database(tests / name, control["tables"])
        gold["controls"].append({"name": control["name"], "database": name, "expected": control["expected"]})
    gold["hashes"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in tests.iterdir() if p.is_file()}
    write_json(tests / "gold.json", gold)
    write_json(tests / "reference.json", definition["reference"])
    if scorer_version == "challenge-1.1.0":
        instruction = definition["instruction"] + COMMON_110.format(
            task_id=task_id,
            claim_tolerances=claim_tolerance_lines(definition),
        ) + UNIT_NORMALIZATION_110
    else:
        instruction = definition["instruction"] + COMMON.format(task_id=task_id)
    (task / "instruction.md").write_text(instruction)
    reference = json.dumps(definition["reference"], indent=2)
    (solution / "solve.sh").write_text("#!/bin/bash\nset -euo pipefail\ncat > /logs/artifacts/answer.json <<'ANSWER'\n" + reference + "\nANSWER\n")
    (tests / "test.sh").write_text("#!/bin/bash\nset -euo pipefail\npython /tests/verify.py\n")
    for name in ("environment/Dockerfile", "tests/Dockerfile", "tests/docker-compose.yaml"):
        shutil.copyfile(ROOT / "tasks/wp01" / name, task / name)
    runtime = json.loads((ROOT / "config/runtime.json").read_text())
    (task / "task.toml").write_text(runtime["task_toml"].replace("{task_id}", task_id))


def build(check=False):
    frozen = set()
    for manifest in (DATASET / "manifests").glob("*.json"):
        frozen.update(json.loads(manifest.read_text()).get("hashes", {}))
    with tempfile.TemporaryDirectory() as temporary:
        staged = Path(temporary)
        count = 0
        for path in sorted((DATASET / "authoring").glob("*/definition.json")):
            definition = json.loads(path.read_text())
            source = json.loads(path.with_name("source_capture.json").read_text())
            extract = path.with_name(source["retained_extract"])
            if hashlib.sha256(extract.read_bytes()).hexdigest() != source["retained_extract_sha256"]:
                raise ValueError("retained_source_extract_changed")
            if not 2 <= len(definition["controls"]) <= 4 or not 4 <= len(definition["evidence"]) <= 10:
                raise ValueError("dossier_or_control_count")
            if not any(a["status"] == "answered" for a in definition["reference"]["answers"]):
                raise ValueError("dossier_requires_answerable_quantity")
            package(definition, staged)
            count += 1
        for path in staged.rglob("*"):
            if not path.is_file():
                continue
            target = DATASET / path.relative_to(staged)
            if check or target.relative_to(ROOT).as_posix() in frozen:
                if not target.is_file():
                    raise ValueError("missing_package_file:" + str(target))
                equal = sqlite_contents(path) == sqlite_contents(target) if path.suffix == ".sqlite" else path.read_bytes() == target.read_bytes()
                if path.name == "gold.json":
                    # Physical SQLite layouts can vary. Hashes bind retained bytes.
                    actual, expected = json.loads(path.read_text()), json.loads(target.read_text())
                    actual["hashes"] = expected["hashes"]
                    equal = actual == expected and all(hashlib.sha256((target.parent / name).read_bytes()).hexdigest() == value for name, value in expected["hashes"].items())
                if not equal:
                    raise ValueError("offline_reconstruction_mismatch:" + str(target))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
        print(f"Reconstructed {count} challenge dossiers offline. " + ("Retained source hashes, typed rows and package contents match." if check else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    build(parser.parse_args().check)
