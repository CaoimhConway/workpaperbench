import hashlib
import json
from pathlib import Path
import shutil

import pytest

from workpaperbench.catalog import content_hash, load, tree_hash

ROOT = Path(__file__).resolve().parents[1]


def test_every_current_task_uses_the_corrected_scorer():
    manifest = load(ROOT)
    assert len(manifest["tasks"]) == 12
    for key in manifest["tasks"]:
        current, task, path = load(ROOT, task=key)
        assert current["scorer_version"] == "challenge-1.1.3"
        assert task["task_id"] == "challenge-v2-" + key
        assert tree_hash(path) == task["task_sha256"]


def test_microsoft_both_candidate_surfaces_have_complete_headings():
    _, _, path = load(ROOT, task="a03")
    sources = (path / "environment/sources.md").read_text()
    evidence = {entry["id"]: entry for entry in json.loads((path / "environment/evidence.json").read_text())}
    for identifier, duration in (("a03:s02", "Three"), ("a03:s03", "Six")):
        section = evidence[identifier]["text"]
        assert duration + " Months Ended December 31," in section
        assert "| Line item | 2024 | 2023 |" in section
        assert "(In millions, except per share amounts) (Unaudited)" in section
        assert section in sources
    assert "recast certain prior period amounts" in sources
    legacy = (ROOT / "datasets/challenge-v1/tasks/a03/environment/sources.md").read_text()
    assert '[["USDmillion except EPS/shares"' in legacy


def test_reviewed_equivalent_evidence_is_in_every_new_gold():
    _, _, nvidia = load(ROOT, task="a02")
    gold = json.loads((nvidia / "tests/gold.json").read_text())
    assert ["a02:s02", "a02:s03"] in gold["answers"]["adjusted_gross_profit"]["evidence"]
    _, _, coinbase = load(ROOT, task="c02")
    assert ["c02:s05"] in json.loads((coinbase / "tests/gold.json").read_text())["conclusion"]["evidence"]


def test_changed_source_cannot_be_blessed_by_a_runtime_profile(tmp_path):
    shutil.copytree(ROOT / "datasets/challenge-v2", tmp_path / "datasets/challenge-v2")
    manifest = json.loads((tmp_path / "datasets/challenge-v2/manifest.json").read_text())
    for name in manifest["hashes"]:
        target = tmp_path / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
    path = tmp_path / "datasets/challenge-v2/tasks/c03/environment/sources.md"
    path.write_text(path.read_text() + "Changed observation\n")
    with pytest.raises(ValueError, match="catalog_task_changed"):
        load(tmp_path, task="c03")


def test_candidate_context_contains_only_declared_assets():
    for key in load(ROOT)["tasks"]:
        _, _, task = load(ROOT, task=key)
        dockerfile = (task / "environment/Dockerfile").read_text()
        assert "COPY data.sqlite evidence.json sources.md schema.json check_answer.py /workspace/" in dockerfile
        assert "COPY . " not in dockerfile
        assert not any(path.name == "__pycache__" for path in task.rglob("*"))
