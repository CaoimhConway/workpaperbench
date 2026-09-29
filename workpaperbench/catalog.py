"""Explicit task and scorer identities for current engineer submissions."""
import hashlib
import json
from pathlib import Path
import re

CHALLENGE_SCORER_SHA256 = 'dfc2a410ce078b404fb3d6723c753ba0134764cb8863fd4377e889e3df40201a'

WORKFLOW_SCORER_SHA256 = 'caf9b58c3e0f1c6ae34cc59546de95b0e0055f872c575db61796ad7ddd1c61aa'


def content_hash(value):
    payload = {key: item for key, item in value.items() if key not in ("manifest_id", "content_hash")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def file_path(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("unsafe_catalog_path")
    current = Path(root)
    for part in Path(relative).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("catalog_symlink")
    return current


def tree_hash(path):
    result = hashlib.sha256()
    if path.is_symlink() or not path.is_dir():
        raise ValueError("catalog_task_directory")
    for item in sorted(path.rglob("*"), key=lambda entry: entry.relative_to(path).as_posix()):
        if item.is_symlink():
            raise ValueError("catalog_task_symlink")
        if item.is_dir():
            continue
        if not item.is_file():
            raise ValueError("catalog_special_file")
        name, data = item.relative_to(path).as_posix().encode(), item.read_bytes()
        result.update(len(name).to_bytes(4, "big") + name + len(data).to_bytes(8, "big") + data)
    return result.hexdigest()


def load(root, dataset="challenge-v2", task=None):
    if dataset not in ('challenge-v2', 'workflow-v1', 'workflow-v2', 'workflow-v3', 'workflow-v4'):
        raise ValueError("unsupported_current_dataset")
    root = Path(root)
    path = file_path(root, "datasets/" + dataset + "/manifest.json")
    manifest = json.loads(path.read_text())
    digest = content_hash(manifest)
    if (manifest.get("dataset_id") != dataset or manifest.get("content_hash") != digest
            or manifest.get("manifest_id") != dataset + "-canonical-" + digest[:12]):
        raise ValueError("catalog_identity_mismatch")
    if dataset == 'challenge-v2' and (manifest.get('scorer_version') != 'challenge-1.1.3'
            or manifest.get('scorer_path') != 'config/scorers/challenge-1.1.3.py'
            or manifest.get('scorer_sha256') != CHALLENGE_SCORER_SHA256):
        raise ValueError('catalog_scorer_identity_mismatch')
    if dataset.startswith('workflow-') and (manifest.get('scorer_version') != 'workflow-1.0.0'
            or manifest.get('scorer_path') != 'workpaperbench/workflow_grading.py'
            or manifest.get('scorer_sha256') != WORKFLOW_SCORER_SHA256):
        raise ValueError('catalog_scorer_identity_mismatch')
    for name, expected in manifest["hashes"].items():
        if hashlib.sha256(file_path(root, name).read_bytes()).hexdigest() != expected:
            raise ValueError("catalog_input_changed:" + name)
    if task is None:
        return manifest
    if not isinstance(task, str) or not re.fullmatch(r"[abc][0-9]{2}", task) or task not in manifest["tasks"]:
        raise ValueError("catalog_task_unknown")
    spec = manifest["tasks"][task]
    task_path = file_path(root, spec["path"])
    if tree_hash(task_path) != spec["task_sha256"]:
        raise ValueError("catalog_task_changed")
    gold = json.loads((task_path / "tests/gold.json").read_text())
    if gold["task_id"] != spec["task_id"] or gold["scorer_version"] != manifest["scorer_version"]:
        raise ValueError("catalog_task_scorer_mismatch")
    module = 'challenge_grading.py' if dataset == 'challenge-v2' else 'workflow_grading.py'
    if hashlib.sha256((task_path / 'tests/workpaperbench' / module).read_bytes()).hexdigest() != manifest["scorer_sha256"]:
        raise ValueError("catalog_embedded_scorer_changed")
    return manifest, spec, task_path
