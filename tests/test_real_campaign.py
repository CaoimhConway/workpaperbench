"""Real-v1 campaign routing and artifact checks using synthetic fixture files."""
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import collect_results
import native_run
import select_slots


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def seal_manifest(manifest):
    content_hash = select_slots.manifest_content_hash(manifest)
    manifest["content_hash"] = content_hash
    manifest["manifest_id"] = "real-v1-" + content_hash[:12]
    return manifest


def fixture_dataset(root):
    base = root / "datasets/real-v1"
    tasks = {}
    source_groups = {}
    hashes = {}
    split_by_task = {"wp01": "development", "wp02": "development", "wp05": "development"}
    for number in (3, 4, 6, 7, 8):
        split_by_task[f"wp{number:02}"] = "evaluation"
    for key, split in split_by_task.items():
        path = base / "tasks" / key
        for name, content in (("task.toml", b"[task]\n"),
                              ("instruction.md", f"Task identifier: real-v1-{key}.\n".encode()),
                              ("environment/data.sqlite", b"fixture"),
                              ("tests/gold.json", json.dumps({"task_id": "real-v1-" + key}).encode())):
            target = path / name
            write(target, content)
            hashes[target.relative_to(root).as_posix()] = hashlib.sha256(content).hexdigest()
        source_group = "source-" + key
        source_groups[key] = source_group
        tasks[key] = {
            "task_id": "real-v1-" + key,
            "path": "datasets/real-v1/tasks/" + key,
            "split": split,
            "origin": "synthetic_fixture",
            "source_group": source_group,
            "previously_exposed": False,
        }
    schedule = []
    for key, split in split_by_task.items():
        for repetition in range(1, 4):
            for arm in ("A", "B"):
                schedule.append({
                    "slot_id": f"final-{key}-{arm}-{repetition}",
                    "campaign": "final", "task": "real-v1-" + key, "arm": arm,
                    "repetition": repetition, "split": split,
                })
    pilot = []
    for key in ("wp01", "wp02", "wp05"):
        for arm in ("A", "B"):
            pilot.append({
                "slot_id": f"pilot-{key}-{arm}-1", "campaign": "pilot",
                "task": "real-v1-" + key, "arm": arm, "repetition": 1,
                "split": "development",
            })
    for relative, value in (("schedule.json", schedule), ("pilot.json", pilot), ("schema.json", {"task_id_pattern": "real-v1-wpID"})):
        content = (json.dumps(value, indent=2) + "\n").encode()
        target = base / relative
        write(target, content)
        hashes[target.relative_to(root).as_posix()] = hashlib.sha256(content).hexdigest()
    for relative in native_run.REAL_RUNTIME_INPUTS:
        content = ("fixture input: " + relative + "\n").encode()
        target = root / relative
        write(target, content)
        hashes[relative] = hashlib.sha256(content).hexdigest()
    capture = base / "captures/filing.html"
    content = b"<html>fixture source capture</html>\n"
    write(capture, content)
    hashes[capture.relative_to(root).as_posix()] = hashlib.sha256(content).hexdigest()
    manifest = {
        "frozen_at": "2026-10-06T00:00:00Z",
        "dataset_id": "real-v1",
        "hashes": hashes,
        "schedule": "datasets/real-v1/schedule.json",
        "pilot": "datasets/real-v1/pilot.json",
        "schema": "datasets/real-v1/schema.json",
        "source_groups": source_groups,
        "tasks": tasks,
    }
    seal_manifest(manifest)
    write(base / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
    return manifest, schedule, pilot


def test_real_campaign_selection_uses_manifest_pilot_and_scoped_slots(tmp_path, monkeypatch):
    manifest, schedule, pilot = fixture_dataset(tmp_path)
    monkeypatch.setattr(select_slots, "ROOT", tmp_path)
    monkeypatch.setattr(select_slots, "history", lambda mode, manifest_id: {})

    baseline, attempted = select_slots.selection("pilot", "real-v1-development", "baseline")
    all_pilot, _ = select_slots.selection("pilot", "real-v1-development", "all")
    final, _ = select_slots.selection("final", manifest["manifest_id"], "all")

    assert [slot["slot_id"] for slot in baseline] == [slot["slot_id"] for slot in pilot if slot["arm"] == "A"]
    assert len(all_pilot) == 6
    assert len(final) == len(schedule) == 48
    assert attempted == {}
    assert all(slot["task"].startswith("real-v1-") for slot in final)


def test_real_freeze_checks_every_current_task_and_campaign_input(tmp_path):
    manifest, _, _ = fixture_dataset(tmp_path)

    loaded = native_run.frozen_inputs(manifest["manifest_id"], root=tmp_path)

    assert loaded["dataset_id"] == "real-v1"
    changed = tmp_path / "datasets/real-v1/tasks/wp01/environment/data.sqlite"
    changed.write_bytes(b"changed after freeze")
    with pytest.raises(ValueError, match="freeze_hash_mismatch"):
        native_run.frozen_inputs(manifest["manifest_id"], root=tmp_path)


def test_real_manifest_rejects_source_groups_shared_across_splits(tmp_path):
    manifest, _, _ = fixture_dataset(tmp_path)
    manifest["source_groups"]["wp03"] = manifest["source_groups"]["wp01"]
    manifest["tasks"]["wp03"]["source_group"] = manifest["source_groups"]["wp03"]
    seal_manifest(manifest)
    (tmp_path / "datasets/real-v1/manifest.json").write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="source_group_cross_split"):
        select_slots.real_dataset_context(manifest["manifest_id"], tmp_path)


def test_real_manifest_rejects_crosswired_task_directory(tmp_path):
    manifest, _, _ = fixture_dataset(tmp_path)
    manifest["tasks"]["wp03"]["path"] = "datasets/real-v1/tasks/wp01"
    seal_manifest(manifest)
    (tmp_path / "datasets/real-v1/manifest.json").write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="dataset_task_path_mismatch"):
        select_slots.real_dataset_context(manifest["manifest_id"], tmp_path)


def test_real_manifest_rejects_mislabeled_task_package(tmp_path):
    manifest, _, _ = fixture_dataset(tmp_path)
    gold = tmp_path / "datasets/real-v1/tasks/wp03/tests/gold.json"
    gold.write_text(json.dumps({"task_id": "real-v1-wp01"}))
    relative = gold.relative_to(tmp_path).as_posix()
    manifest["hashes"][relative] = hashlib.sha256(gold.read_bytes()).hexdigest()
    seal_manifest(manifest)
    (tmp_path / "datasets/real-v1/manifest.json").write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="dataset_task_package_identity_mismatch"):
        select_slots.real_dataset_context(manifest["manifest_id"], tmp_path)


def test_real_manifest_hash_binds_frozen_input_hashes(tmp_path):
    manifest, _, _ = fixture_dataset(tmp_path)
    instruction = tmp_path / "datasets/real-v1/tasks/wp01/instruction.md"
    instruction.write_text("changed and rehashed after freeze\n")
    manifest["hashes"][instruction.relative_to(tmp_path).as_posix()] = hashlib.sha256(instruction.read_bytes()).hexdigest()
    (tmp_path / "datasets/real-v1/manifest.json").write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="dataset_content_hash_mismatch"):
        native_run.frozen_inputs(manifest["manifest_id"], root=tmp_path)


def test_authenticated_pilot_pair_import_uses_dataset_schedule_and_namespace(tmp_path):
    manifest, _, pilot = fixture_dataset(tmp_path)
    slot = pilot[0]
    run = {"id": 51, "head_sha": "a" * 40, "run_attempt": 1}
    record = {
        **slot,
        "experiment_id": "real-v1-development",
        "dataset_id": "real-v1",
        "dataset_manifest_id": manifest["manifest_id"],
        "freeze_manifest_id": None,
        "run_id": "51",
        "github_run_attempt": "1",
        "commit_sha": "a" * 40,
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("record.json", json.dumps(record))
        archive.writestr("answer.json", "{}\n")
    data = buffer.getvalue()
    artifact = {
        "id": 91,
        "digest": "sha256:" + hashlib.sha256(data).hexdigest(),
        "declared_slots": [slot["slot_id"]],
        "manifest_id": "real-v1-development",
        "campaign": "pilot",
        "workflow_run": {"id": 51, "head_sha": "a" * 40, "run_attempt": 1},
    }

    assert collect_results.import_archive(data, artifact, tmp_path) == [slot["slot_id"]]
    saved = tmp_path / "reports/runs/real-v1-development" / slot["slot_id"] / "record.json"
    assert saved.is_file()


def test_pilot_pair_artifact_attempt_authenticates_both_declared_slots(monkeypatch):
    run = {"id": 8, "head_sha": "b" * 40, "run_attempt": 2}
    artifact = {
        "name": "pair-real-v1-development-8-1-pilot-wp01-A-1--pilot-wp02-B-1",
        "workflow_run": {"id": 8, "head_sha": "b" * 40},
    }
    monkeypatch.setattr(collect_results, "api", lambda _: {**run, "run_attempt": 1})

    collect_results.authenticate_attempt(artifact, run, "real-v1-development", {}, "pilot")

    assert artifact["declared_slots"] == ["pilot-wp01-A-1", "pilot-wp02-B-1"]
    assert artifact["campaign"] == "pilot"
    assert artifact["workflow_run"]["run_attempt"] == 1


def provider_archive_fixture(run_id):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("provider.json", json.dumps({"run_id": run_id, "snapshot": {}}))
    data = buffer.getvalue()
    return data, {
        "id": 101,
        "digest": "sha256:" + hashlib.sha256(data).hexdigest(),
        "workflow_run": {"id": run_id},
    }


def test_real_provider_receipt_stays_out_of_historical_report_path(tmp_path):
    manifest, _, _ = fixture_dataset(tmp_path)
    run = {"id": 52}
    data, artifact = provider_archive_fixture(run["id"])
    artifact["manifest_id"] = manifest["manifest_id"]

    collect_results.provider_archive(data, artifact, run, tmp_path)

    assert (tmp_path / "reports/real-v1/provider/52.json").is_file()
    assert not (tmp_path / "reports/provider/52.json").exists()


def test_legacy_provider_receipt_keeps_historical_path(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/freeze.json").write_text(json.dumps({"manifest_id": "legacy"}))
    run = {"id": 53}
    data, artifact = provider_archive_fixture(run["id"])
    artifact["manifest_id"] = "legacy"

    collect_results.provider_archive(data, artifact, run, tmp_path)

    assert (tmp_path / "reports/provider/53.json").is_file()
    assert not (tmp_path / "reports/real-v1/provider/53.json").exists()


def test_reconciliation_outputs_are_campaign_scoped_for_real_v1(tmp_path):
    manifest, _, _ = fixture_dataset(tmp_path)
    context = select_slots.campaign_context(manifest["manifest_id"], tmp_path)

    assert collect_results.reconciliation_path(tmp_path, context, "pilot") == (
        tmp_path / "reports/real-v1/pilot-reconciliation.json")
    assert collect_results.reconciliation_path(tmp_path, context, "final") == (
        tmp_path / "reports/real-v1/final-reconciliation.json")


def test_legacy_reconciliation_keeps_historical_path(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/freeze.json").write_text(json.dumps({"manifest_id": "legacy"}))
    context = select_slots.campaign_context("legacy", tmp_path)

    assert collect_results.reconciliation_path(tmp_path, context, "final") == (
        tmp_path / "reports/reconciliation.json")
