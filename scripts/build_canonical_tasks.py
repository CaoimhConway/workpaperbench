"""Build a new reusable corrected challenge release without changing history."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from build_challenge_tasks import COMMON_110, UNIT_NORMALIZATION_110, claim_tolerance_lines
from challenge_evidence_review import validate_review
from fresh_replay import tree_sha256
from select_slots import manifest_content_hash

ROOT = Path(__file__).resolve().parents[1]
SCORER = "challenge-1.1.3"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def construct(destination, root=ROOT):
    root, destination = Path(root), Path(destination)
    reviewed = validate_review(root)
    old = root / "datasets/challenge-v1"
    current = root / "datasets/challenge-v2"
    capture = json.loads((current / "microsoft-source-capture.json").read_text())
    extract = current / capture["retained_extract"]
    if hashlib.sha256(extract.read_bytes()).hexdigest() != capture["retained_extract_sha256"]:
        raise ValueError("canonical_source_extract_changed")
    schema = json.loads((root / "config/schemas/challenge-1.1.0.json").read_text())
    schema["properties"]["task_id"]["pattern"] = "^challenge-v2-[abc]0[1-4]$"
    tasks = {}
    for key in sorted(path.name for path in (old / "tasks").iterdir() if path.is_dir()):
        source = old / "tasks" / key
        task = destination / "tasks" / key
        shutil.copytree(source, task, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "._*"))
        origin_hash = tree_sha256(task)
        identifier = "challenge-v2-" + key
        definition = json.loads((old / "authoring" / key / "definition.json").read_text())
        gold = json.loads((task / "tests/gold.json").read_text())
        gold["task_id"], gold["scorer_version"] = identifier, SCORER
        additions = reviewed["review"]["tasks"].get(key, {}).get("additional_evidence_paths", {})
        for claim_id, options in additions.items():
            claim = gold["conclusion"] if claim_id == "conclusion" else gold["answers"][claim_id]
            for option in options:
                if option not in claim["evidence"]:
                    claim["evidence"].append(option)
        reference = json.loads((task / "tests/reference.json").read_text())
        reference["task_id"] = identifier
        write_json(task / "tests/reference.json", reference)
        for folder in ("environment", "tests"):
            write_json(task / folder / "schema.json", schema)
            if key == "a03":
                (task / folder / "sources.md").write_bytes(extract.read_bytes())
                evidence_path = task / folder / "evidence.json"
                evidence = json.loads(evidence_path.read_text())
                refreshed = {item["id"]: item for item in capture["sources"]}
                for item in evidence:
                    entry = refreshed[item["id"]]
                    for field in ("retrieved_at", "source_bytes_sha256"):
                        if field in item:
                            item[field] = entry[field]
                    item["capture_sha256"] = capture["retained_extract_sha256"]
                    start = extract.read_text().index(item["id"] + " -")
                    section = extract.read_text()[start:].split("\n", 1)[1]
                    next_section = section.find("\na03:")
                    item["text"] = section[:next_section].rstrip() if next_section >= 0 else section.split("\n## Data dictionary", 1)[0].rstrip()
                write_json(evidence_path, evidence)
        (task / "tests/workpaperbench/challenge_grading.py").write_bytes(
            (root / "config/scorers/challenge-1.1.3.py").read_bytes())
        verifier = (task / "tests/verify.py").read_text()
        verifier = verifier.replace(
            'if any(k in os.environ for k in ("OPENROUTER_API_KEY", "GITHUB_TOKEN", "GH_TOKEN")):',
            'if any(k.endswith("API_KEY") or k in ("GITHUB_TOKEN", "GH_TOKEN") for k in os.environ):')
        verifier = verifier.replace(
            '"no_inference_key": "OPENROUTER_API_KEY" not in os.environ,',
            '"no_inference_key": not any(k.endswith("API_KEY") for k in os.environ),')
        (task / "tests/verify.py").write_text(verifier)
        gold["hashes"] = {name: hashlib.sha256((task / "tests" / name).read_bytes()).hexdigest()
                          for name in gold["hashes"]}
        write_json(task / "tests/gold.json", gold)
        instruction = definition["instruction"] + COMMON_110.format(
            task_id=identifier, claim_tolerances=claim_tolerance_lines(definition)) + UNIT_NORMALIZATION_110
        (task / "instruction.md").write_text(instruction)
        (task / "solution/solve.sh").write_text(
            "#!/bin/bash\nset -euo pipefail\ncat > /logs/artifacts/answer.json <<'ANSWER'\n"
            + json.dumps(reference, indent=2) + "\nANSWER\n")
        toml = (task / "task.toml").read_text().replace("challenge-v1-" + key, identifier)
        toml = toml.replace('allowed_hosts = ["openrouter.ai"]', 'allowed_hosts = ["172.17.0.1"]')
        (task / "task.toml").write_text(toml)
        tasks[key] = {
            "task_id": identifier, "path": "datasets/challenge-v2/tasks/" + key,
            "task_sha256": tree_sha256(task), "origin_task_sha256": origin_hash,
            "split": "development" if key.endswith("01") else "published_regression",
            "exposure": "Previously published source case, never newly held out",
            "source_group": definition["source_group"],
        }
    manifest = {
        "dataset_id": "challenge-v2", "scorer_version": SCORER,
        "scorer_path": "config/scorers/challenge-1.1.3.py",
        "scorer_sha256": hashlib.sha256((root / "config/scorers/challenge-1.1.3.py").read_bytes()).hexdigest(),
        "correction_origin": reviewed["review"]["review_id"],
        "microsoft_snapshot": capture["snapshot_id"], "tasks": tasks,
        "execution_profile": "local-lima", "historical_scores_rewritten": False,
        "hashes": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in (
            "scripts/build_canonical_tasks.py", "config/scorers/challenge-1.1.3.py",
            "workpaperbench/grading.py", "workpaperbench/challenge_sql_worker.py",
            "datasets/challenge-v2/microsoft-source-extracts.md",
            "datasets/challenge-v2/microsoft-source-capture.json")},
    }
    manifest["content_hash"] = manifest_content_hash(manifest)
    manifest["manifest_id"] = "challenge-v2-canonical-" + manifest["content_hash"][:12]
    write_json(destination / "manifest.json", manifest)
    return manifest


def build(check=False, root=ROOT):
    destination = Path(root) / "datasets/challenge-v2"
    with tempfile.TemporaryDirectory() as temporary:
        staged = Path(temporary)
        manifest = construct(staged, root)
        for path in sorted(staged.rglob("*")):
            if not path.is_file():
                continue
            target = destination / path.relative_to(staged)
            if check:
                if not target.is_file() or target.is_symlink() or path.read_bytes() != target.read_bytes():
                    raise ValueError("canonical_reconstruction_mismatch:" + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError("canonical_release_exists_with_different_bytes")
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.write_bytes(path.read_bytes())
    print(manifest["manifest_id"], len(manifest["tasks"]), "corrected dossiers verified" if check else "corrected dossiers built")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    build(parser.parse_args().check)
