"""Manifest, slot, reservation, and retention checks for challenge-v1."""
import hashlib
import importlib.util
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import attempts
import check_install
import collect_results
import native_run
import native_trial
import select_slots


MODELS = {
    "inexpensive": {
        "id": "vendor/cheap-tools",
        "harbor_model": "openrouter/vendor/cheap-tools",
        "provider": "openrouter",
        "route_policy": "fixed test route",
        "reservation_usd_per_slot": 0.10,
    },
    "reference": {
        "id": "vendor/reference-tools",
        "harbor_model": "openrouter/vendor/reference-tools",
        "provider": "openrouter",
        "route_policy": "fixed test route",
        "reservation_usd_per_slot": 0.40,
    },
}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def make_stage(root, stage, *, groups=None, models=None, filename=None,
               development_manifest_id=None, future_tag=None):
    campaign = "pilot" if stage == "development" else "final"
    keys = select_slots.CHALLENGE_TASKS[campaign]
    split = "development" if campaign == "pilot" else "evaluation"
    groups = groups or {key: f"source-{key}" for key in keys}
    models = models or MODELS
    tasks = {}
    hashes = {}
    for key in keys:
        task_id = f"challenge-v1-{key}"
        task_path = f"datasets/challenge-v1/tasks/{key}"
        instruction = root / task_path / "instruction.md"
        gold = root / task_path / "tests/gold.json"
        instruction.parent.mkdir(parents=True, exist_ok=True)
        instruction.write_text("Complete the bounded research workpaper.\n")
        write_json(gold, {"task_id": task_id})
        for path in (instruction, gold):
            hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        tasks[key] = {
            "task_id": task_id,
            "path": task_path,
            "split": split,
            "source_group": groups[key],
            "origin": "synthetic_fixture",
        }

    schedule = []
    for key in keys:
        for repetition in (1, 2, 3):
            for model_key in ("inexpensive", "reference"):
                schedule.append({
                    "slot_id": f"{campaign}-{key}-{model_key}-{repetition}",
                    "campaign": campaign,
                    "task": f"challenge-v1-{key}",
                    "model_key": model_key,
                    "condition": "full",
                    "repetition": repetition,
                    "split": split,
                })
    schedule_path = f"datasets/challenge-v1/schedules/{stage}.json"
    schema_path = "datasets/challenge-v1/schema.json"
    schema_file = root / schema_path
    write_json(schema_file, {"type": "object"})
    schedule_file = root / schedule_path
    write_json(schedule_file, schedule)
    for path in (schema_file, schedule_file):
        hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        "dataset_id": "challenge-v1",
        "stage": campaign,
        "schedule": schedule_path,
        "schema": schema_path,
        "tasks": tasks,
        "models": models,
        "budget": {"reservation_usd": 9.0},
        "hashes": hashes,
    }
    if development_manifest_id:
        manifest["development_manifest_id"] = development_manifest_id
    if future_tag:
        manifest["future_tag"] = future_tag
    manifest["content_hash"] = select_slots.manifest_content_hash(manifest)
    manifest["manifest_id"] = f"challenge-v1-{stage}-{manifest['content_hash'][:12]}"
    manifest_path = root / "datasets/challenge-v1/manifests" / (filename or f"{stage}.json")
    write_json(manifest_path, manifest)
    return manifest, schedule


def pair_slots(schedule, task, repetition):
    return [slot for slot in schedule if slot["task"] == task and slot["repetition"] == repetition]


def install_current_run_pairs(monkeypatch, manifest_id, active, completed, queued, run_id=51):
    run = {"id": run_id, "display_title": f"WPB::{manifest_id}::pilot"}

    def job(slots, status, *, runner_id=None):
        return {
            "id": {"completed": 100, "in_progress": 101, "queued": 102}[status],
            "name": "pair-" + manifest_id + "-" + "--".join(slot["slot_id"] for slot in slots),
            "status": status,
            "conclusion": "success" if status == "completed" else None,
            "runner_id": runner_id,
            "run_attempt": 1,
            "started_at": "2026-10-06T00:00:00Z" if runner_id else None,
        }

    jobs = [job(completed, "completed", runner_id=1), job(active, "in_progress", runner_id=2),
            job(queued, "queued")]

    def pages(_path, key):
        return iter([run] if key == "workflow_runs" else jobs)

    monkeypatch.setattr(select_slots, "pages", pages)
    monkeypatch.setenv("GITHUB_RUN_ID", str(run_id))
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("WPB_SLOTS", json.dumps([slot["slot_id"] for slot in active]))


def test_challenge_manifests_select_balanced_full_dossier_slots(tmp_path, monkeypatch):
    development, pilot = make_stage(tmp_path, "development")
    evaluation, final = make_stage(tmp_path, "evaluation")
    monkeypatch.setattr(select_slots, "ROOT", tmp_path)
    monkeypatch.setattr(select_slots, "history", lambda mode, manifest_id: {})

    context = select_slots.campaign_context(development["manifest_id"], tmp_path)
    final_context = select_slots.campaign_context(evaluation["manifest_id"], tmp_path)
    selected, attempted = select_slots.selection("pilot", development["manifest_id"], "all")
    jobs = select_slots.pairs(selected)

    assert context["dataset_id"] == "challenge-v1"
    assert context["stage"] == "pilot"
    assert final_context["stage"] == "final"
    assert len(select_slots.campaign_slots(context, "pilot")) == len(pilot) == 18
    assert len(select_slots.campaign_slots(final_context, "final")) == len(final) == 54
    assert len(selected) == 18 and attempted == {}
    assert len(jobs) == 9 and all(len(job["slots"]) == 2 for job in jobs)
    assert all("-inexpensive-" in job["slots"][0] and "-reference-" in job["slots"][1]
               for job in jobs)
    with pytest.raises(ValueError, match="batch_all"):
        select_slots.selection("pilot", development["manifest_id"], "baseline")


def test_challenge_manifests_reject_tampering_bad_schedule_and_cross_split_sources(tmp_path):
    development, _ = make_stage(tmp_path, "development")
    evaluation, _ = make_stage(tmp_path, "evaluation")
    final_path = tmp_path / "datasets/challenge-v1/manifests/evaluation.json"
    malformed = json.loads(final_path.read_text())
    malformed["tasks"]["a02"]["source_group"] = "source-a01"
    malformed["content_hash"] = select_slots.manifest_content_hash(malformed)
    malformed["manifest_id"] = "challenge-v1-evaluation-" + malformed["content_hash"][:12]
    write_json(final_path, malformed)
    with pytest.raises(ValueError, match="cross_split"):
        select_slots.challenge_dataset_context(malformed["manifest_id"], tmp_path)

    malformed["tasks"]["a02"]["source_group"] = "source-a02"
    malformed["content_hash"] = select_slots.manifest_content_hash(malformed)
    malformed["manifest_id"] = "challenge-v1-evaluation-" + malformed["content_hash"][:12]
    final_path.write_text(json.dumps(malformed, indent=2) + "\n")
    schedule_path = tmp_path / malformed["schedule"]
    schedule = json.loads(schedule_path.read_text())
    schedule.pop()
    write_json(schedule_path, schedule)
    with pytest.raises(ValueError, match="schedule_count"):
        context = select_slots.challenge_dataset_context(malformed["manifest_id"], tmp_path)
        select_slots.campaign_slots(context, "final")
    assert development["manifest_id"].startswith("challenge-v1-development-")
    assert evaluation["manifest_id"].startswith("challenge-v1-evaluation-")


def test_future_challenge_manifest_is_explicit_and_does_not_replace_stage_freeze(tmp_path, monkeypatch):
    original_development, _ = make_stage(tmp_path, "development")
    versioned_development, _ = make_stage(
        tmp_path, "development", filename="development-future.json", future_tag="second-route")
    # The filename is an explicit stage-manifest path. The evaluation freeze binds it.
    versioned_path = tmp_path / "datasets/challenge-v1/manifests" / (
        "development-" + versioned_development["content_hash"][:12] + ".json")
    versioned_path.write_text(json.dumps(versioned_development, indent=2) + "\n")
    versioned_development["manifest_id"] = "challenge-v1-development-" + versioned_development["content_hash"][:12]
    evaluation, _ = make_stage(
        tmp_path, "evaluation", development_manifest_id=versioned_development["manifest_id"])

    context = select_slots.challenge_dataset_context(evaluation["manifest_id"], tmp_path)
    versioned_context = select_slots.challenge_dataset_context(
        versioned_development["manifest_id"], tmp_path)
    monkeypatch.setattr(select_slots, "ROOT", tmp_path)
    monkeypatch.setattr(select_slots, "history", lambda mode, manifest_id: {})
    fresh_slots, attempted = select_slots.selection(
        "pilot", versioned_development["manifest_id"], "all")

    assert context["manifest"]["development_manifest_id"] == versioned_development["manifest_id"]
    assert original_development["manifest_id"] != versioned_development["manifest_id"]
    assert versioned_context["manifest_path"] == versioned_path
    assert len(fresh_slots) == 18 and attempted == {}
    assert (tmp_path / "datasets/challenge-v1/manifests/development.json").is_file()


def test_new_campaign_helper_creates_hashed_profiles_without_changing_original_freezes(tmp_path, monkeypatch):
    development, _ = make_stage(tmp_path, "development")
    evaluation, _ = make_stage(tmp_path, "evaluation")
    profile_file = tmp_path / "models/future-profiles.json"
    write_json(profile_file, MODELS)
    original_bytes = {
        "development": (tmp_path / "datasets/challenge-v1/manifests/development.json").read_bytes(),
        "evaluation": (tmp_path / "datasets/challenge-v1/manifests/evaluation.json").read_bytes(),
    }
    monkeypatch.setattr(native_run, "ROOT", tmp_path)
    monkeypatch.setattr(native_run, "CHALLENGE_RUNTIME_INPUTS", set())
    monkeypatch.setattr(select_slots, "ROOT", tmp_path)
    monkeypatch.setattr(select_slots, "history", lambda mode, manifest_id: {})
    import new_challenge_campaign

    outputs = new_challenge_campaign.create(profile_file, tmp_path)
    outputs_again = new_challenge_campaign.create(profile_file, tmp_path)

    assert len(outputs) == 2
    assert outputs_again == outputs
    assert (tmp_path / "datasets/challenge-v1/manifests/development.json").read_bytes() == original_bytes["development"]
    assert (tmp_path / "datasets/challenge-v1/manifests/evaluation.json").read_bytes() == original_bytes["evaluation"]
    future_development, future_evaluation = [json.loads(path.read_text()) for path in outputs]
    assert future_development["base_manifest_id"] == development["manifest_id"]
    assert future_evaluation["base_manifest_id"] == evaluation["manifest_id"]
    assert future_evaluation["development_manifest_id"] == future_development["manifest_id"]
    assert future_development["hashes"]["models/future-profiles.json"] == hashlib.sha256(profile_file.read_bytes()).hexdigest()


def test_challenge_freeze_binds_current_stage_packages_and_runtime(tmp_path, monkeypatch):
    manifest, _ = make_stage(tmp_path, "development")
    monkeypatch.setattr(native_run, "ROOT", tmp_path)
    monkeypatch.setattr(native_run, "CHALLENGE_RUNTIME_INPUTS", set())

    loaded = native_run.frozen_inputs(manifest["manifest_id"], root=tmp_path)

    assert loaded["manifest_id"] == manifest["manifest_id"]
    changed = tmp_path / manifest["tasks"]["a01"]["path"] / "instruction.md"
    changed.write_text("changed after freeze\n")
    with pytest.raises(ValueError, match="freeze_hash_mismatch"):
        native_run.frozen_inputs(manifest["manifest_id"], root=tmp_path)


def test_future_campaign_uses_frozen_final_runtime_without_rebinding_pilot(tmp_path, monkeypatch):
    development, _ = make_stage(tmp_path, "development")
    runtime_name = "scripts/fix_native_version.py"
    runtime_file = tmp_path / runtime_name
    runtime_file.parent.mkdir(parents=True, exist_ok=True)
    runtime_file.write_text("original pinned correction\n")
    development["hashes"][runtime_name] = hashlib.sha256(runtime_file.read_bytes()).hexdigest()
    development["content_hash"] = select_slots.manifest_content_hash(development)
    development["manifest_id"] = "challenge-v1-development-" + development["content_hash"][:12]
    development_path = tmp_path / "datasets/challenge-v1/manifests/development.json"
    write_json(development_path, development)
    original_bytes = development_path.read_bytes()
    runtime_file.write_text("reviewed post-config observer correction\n")
    evaluation, _ = make_stage(
        tmp_path, "evaluation", development_manifest_id=development["manifest_id"])
    evaluation["hashes"][runtime_name] = hashlib.sha256(runtime_file.read_bytes()).hexdigest()
    evaluation["content_hash"] = select_slots.manifest_content_hash(evaluation)
    evaluation["manifest_id"] = "challenge-v1-evaluation-" + evaluation["content_hash"][:12]
    write_json(tmp_path / "datasets/challenge-v1/manifests/evaluation.json", evaluation)
    profile_file = tmp_path / "models/future-profiles.json"
    write_json(profile_file, MODELS)
    monkeypatch.setattr(native_run, "CHALLENGE_RUNTIME_INPUTS", set())
    import new_challenge_campaign

    outputs = new_challenge_campaign.create(profile_file, tmp_path)
    future = json.loads(outputs[0].read_text())
    assert future["runtime_manifest_id"] == evaluation["manifest_id"]
    assert future["runtime_changes"][runtime_name] == {
        "original": development["hashes"][runtime_name],
        "current": evaluation["hashes"][runtime_name],
    }
    assert development_path.read_bytes() == original_bytes
    assert native_run.frozen_inputs(future["manifest_id"], tmp_path) == future
    with pytest.raises(ValueError, match="freeze_hash_mismatch"):
        native_run.frozen_inputs(development["manifest_id"], tmp_path)
    runtime_file.write_text("unfrozen operational edit\n")
    with pytest.raises(ValueError, match="freeze_hash_mismatch"):
        new_challenge_campaign.create(profile_file, tmp_path)
    runtime_file.write_text("reviewed post-config observer correction\n")
    instruction = tmp_path / development["tasks"]["a01"]["path"] / "instruction.md"
    instruction.write_text("changed candidate instructions\n")
    with pytest.raises(ValueError, match="freeze_hash_mismatch"):
        new_challenge_campaign.create(profile_file, tmp_path)


def test_challenge_operations_review_is_key_free_and_cannot_change_cases(tmp_path, monkeypatch):
    manifest, _ = make_stage(tmp_path, "development")
    relative = "scripts/fix_native_version.py"
    runtime = tmp_path / relative
    runtime.parent.mkdir(parents=True, exist_ok=True)
    runtime.write_text("original native correction\n")
    manifest["hashes"][relative] = hashlib.sha256(runtime.read_bytes()).hexdigest()
    manifest["content_hash"] = select_slots.manifest_content_hash(manifest)
    manifest["manifest_id"] = "challenge-v1-development-" + manifest["content_hash"][:12]
    path = tmp_path / "datasets/challenge-v1/manifests/development.json"
    write_json(path, manifest)
    runtime.write_text("reviewed observer correction\n")
    helper = tmp_path / "scripts/operations_review.py"
    helper.write_bytes((ROOT / "scripts/operations_review.py").read_bytes())
    review = {
        "original_manifest_id": manifest["manifest_id"],
        "original_manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "correction_hashes": {relative: hashlib.sha256(runtime.read_bytes()).hexdigest()},
        "review_helper_sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
    }
    review_path = tmp_path / "datasets/challenge-v1/operations-review.json"
    write_json(review_path, review)
    monkeypatch.setattr(native_run, "CHALLENGE_RUNTIME_INPUTS", set())

    assert native_run.frozen_inputs(manifest["manifest_id"], tmp_path, reviewed_operations=True) == manifest
    with pytest.raises(ValueError, match="freeze_hash_mismatch"):
        native_run.frozen_inputs(manifest["manifest_id"], tmp_path)
    original_helper = helper.read_bytes()
    helper.write_bytes(original_helper + b"\n")
    with pytest.raises(ValueError, match="challenge_review_helper_changed"):
        native_run.frozen_inputs(manifest["manifest_id"], tmp_path, reviewed_operations=True)
    helper.write_bytes(original_helper)
    runtime.write_text("unreviewed native change\n")
    with pytest.raises(ValueError, match="freeze_hash_mismatch"):
        native_run.frozen_inputs(manifest["manifest_id"], tmp_path, reviewed_operations=True)
    instruction = manifest["tasks"]["a01"]["path"] + "/instruction.md"
    review["correction_hashes"][instruction] = manifest["hashes"][instruction]
    write_json(review_path, review)
    with pytest.raises(ValueError, match="challenge_operations_review_invalid"):
        native_run.frozen_inputs(manifest["manifest_id"], tmp_path, reviewed_operations=True)


def test_challenge_manifest_and_packaged_scorer_versions_must_match(tmp_path):
    manifest, _ = make_stage(tmp_path, "development")
    gold = tmp_path / manifest["tasks"]["a01"]["path"] / "tests/gold.json"
    write_json(gold, {"task_id": "challenge-v1-a01", "scorer_version": "challenge-1.1.0"})
    with pytest.raises(ValueError, match="challenge_task_scorer_version_mismatch"):
        select_slots.challenge_dataset_context(manifest["manifest_id"], tmp_path)


def test_challenge_reservation_sums_remaining_model_costs_without_multiplier(tmp_path):
    manifest, schedule = make_stage(tmp_path, "development")
    context = select_slots.challenge_dataset_context(manifest["manifest_id"], tmp_path)
    first = schedule[0]
    second = schedule[1]
    records = [{**first, "experiment_id": manifest["manifest_id"], "status": "task_failed"}]

    reserve, count = native_run.challenge_reservation(
        context, "pilot", second["slot_id"], {first["slot_id"]: {}}, records)

    assert count == 17
    assert reserve == pytest.approx(4.4)


def test_history_excludes_only_active_pair_and_keeps_started_pairs_in_same_run(tmp_path, monkeypatch):
    manifest, schedule = make_stage(tmp_path, "development")
    completed = pair_slots(schedule, "challenge-v1-a01", 1)
    active = pair_slots(schedule, "challenge-v1-a01", 2)
    queued = pair_slots(schedule, "challenge-v1-a01", 3)
    install_current_run_pairs(monkeypatch, manifest["manifest_id"], active, completed, queued)

    attempted = select_slots.history("pilot", manifest["manifest_id"])

    assert set(attempted) == {slot["slot_id"] for slot in completed}
    monkeypatch.delenv("WPB_SLOTS")
    assert select_slots.history("pilot", manifest["manifest_id"]) == {}


def test_clean_checkout_reservation_drops_completed_same_run_pair(tmp_path, monkeypatch):
    manifest, schedule = make_stage(tmp_path, "development")
    context = select_slots.challenge_dataset_context(manifest["manifest_id"], tmp_path)
    completed = pair_slots(schedule, "challenge-v1-a01", 1)
    active = pair_slots(schedule, "challenge-v1-a01", 2)
    queued = pair_slots(schedule, "challenge-v1-a01", 3)
    install_current_run_pairs(monkeypatch, manifest["manifest_id"], active, completed, queued)
    attempted = select_slots.history("pilot", manifest["manifest_id"])

    reserve, count = native_run.challenge_reservation(
        context, "pilot", active[0]["slot_id"], attempted, records=[])

    expected = sum(
        MODELS[slot["model_key"]]["reservation_usd_per_slot"]
        for slot in schedule if slot["slot_id"] not in {item["slot_id"] for item in completed}
    )
    assert count == 16
    assert reserve == pytest.approx(expected)


def test_challenge_attempt_receipt_and_collection_authenticate_model_condition(tmp_path, monkeypatch):
    manifest, schedule = make_stage(tmp_path, "development")
    monkeypatch.setattr(select_slots, "ROOT", tmp_path)
    monkeypatch.setattr(attempts, "ROOT", tmp_path)
    monkeypatch.setattr(select_slots, "history", lambda mode, manifest_id: {})
    monkeypatch.setenv("GITHUB_RUN_ID", "51")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)

    pair = pair_slots(schedule, "challenge-v1-a01", 1)
    attempts.receipt("pilot", manifest["manifest_id"], [slot["slot_id"] for slot in pair])
    assert attempts.check("pilot", manifest["manifest_id"], [pair[0]["slot_id"]]) == {}
    shutil.rmtree(tmp_path / "reports/runs" / manifest["manifest_id"])

    run = {"id": 51, "head_sha": "a" * 40, "run_attempt": 1}
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as output:
        for slot in pair:
            record = {
                **slot,
                "experiment_id": manifest["manifest_id"],
                "dataset_id": "challenge-v1",
                "dataset_manifest_id": manifest["manifest_id"],
                "source_group": manifest["tasks"][slot["task"].removeprefix("challenge-v1-")]["source_group"],
                "task_origin": manifest["tasks"][slot["task"].removeprefix("challenge-v1-")]["origin"],
                "model": manifest["models"][slot["model_key"]]["id"],
                "model_route_policy": manifest["models"][slot["model_key"]]["route_policy"],
                "model_provider": manifest["models"][slot["model_key"]]["provider"],
                "model_harbor_model": manifest["models"][slot["model_key"]]["harbor_model"],
                "reservation_usd_per_slot": manifest["models"][slot["model_key"]]["reservation_usd_per_slot"],
                "freeze_manifest_id": None,
                "run_id": "51",
                "github_run_attempt": "1",
                "commit_sha": "a" * 40,
                "status": "task_failed",
            }
            output.writestr(slot["slot_id"] + "/record.json", json.dumps(record))
    data = archive.getvalue()
    artifact = {
        "id": 91,
        "name": "pair-" + manifest["manifest_id"] + "-51-1-" + "--".join(s["slot_id"] for s in pair),
        "digest": "sha256:" + hashlib.sha256(data).hexdigest(),
        "workflow_run": {"id": 51, "head_sha": "a" * 40, "run_attempt": 1},
    }
    collect_results.authenticate_attempt(artifact, run, manifest["manifest_id"], {}, "pilot")
    assert artifact["declared_slots"] == [slot["slot_id"] for slot in pair]
    assert collect_results.import_archive(data, artifact, tmp_path) == [slot["slot_id"] for slot in pair]
    record["model"] = "forged/model"
    with pytest.raises(ValueError, match="challenge_provenance_mismatch"):
        collect_results.validate_record(record, tmp_path, run, manifest["manifest_id"], "pilot")


def test_challenge_setup_failure_receipt_preserves_declared_provenance_for_collection(tmp_path, monkeypatch):
    manifest, schedule = make_stage(tmp_path, "development")
    monkeypatch.setattr(select_slots, "ROOT", tmp_path)
    monkeypatch.setattr(attempts, "ROOT", tmp_path)
    monkeypatch.setattr(select_slots, "history", lambda mode, manifest_id: {})
    monkeypatch.setenv("GITHUB_RUN_ID", "51")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)

    pair = pair_slots(schedule, "challenge-v1-a01", 1)
    attempts.receipt("pilot", manifest["manifest_id"], [slot["slot_id"] for slot in pair])
    attempts.finalize(manifest["manifest_id"], [slot["slot_id"] for slot in pair])
    run = {"id": 51, "head_sha": "a" * 40, "run_attempt": 1}

    for slot in pair:
        record_path = (tmp_path / "reports/runs" / manifest["manifest_id"]
                       / slot["slot_id"] / "record.json")
        record = json.loads(record_path.read_text())
        task_key = slot["task"].removeprefix("challenge-v1-")
        task = manifest["tasks"][task_key]
        model = manifest["models"][slot["model_key"]]

        assert record["status"] == "infra_failed"
        assert record["verdict"] is None
        assert "native_return_code" not in record
        assert record["model_profile_status"] == "manifest_declared_not_execution_evidence"
        assert record["source_group"] == task["source_group"]
        assert record["task_origin"] == task["origin"]
        assert record["model"] == model["id"]
        assert record["model_route_policy"] == model["route_policy"]
        assert record["model_provider"] == model["provider"]
        assert record["model_harbor_model"] == model["harbor_model"]
        assert record["reservation_usd_per_slot"] == model["reservation_usd_per_slot"]
        assert collect_results.validate_record(
            record, tmp_path, run, manifest["manifest_id"], "pilot") == slot


def test_native_retry_observer_records_only_bounded_metadata_and_counts_repeated_starts(tmp_path, monkeypatch):
    plugin_path = ROOT / "config/native-api-observer/__init__.py"
    spec = importlib.util.spec_from_file_location("native_api_observer_test", plugin_path)
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    ledger = tmp_path / ".raw/native-api-observer.jsonl"
    observer._events = 0
    observer._request_attempts.clear()
    monkeypatch.setattr(observer, "_ledger_path", lambda: ledger)
    monkeypatch.setattr(native_run, "ROOT", tmp_path)
    hooks = {}

    class Context:
        def register_hook(self, name, callback):
            hooks[name] = callback

    observer.register(Context())
    request_id = "turn-secret-shape:api:4"
    hooks["pre_api_request"](
        api_request_id=request_id, api_call_count=4, retry_count=0, max_retries=5,
        started_at=1_800_000_000.0, user_message="never retain this", request={"body": "private"})
    hooks["api_request_error"](
        api_request_id=request_id, api_call_count=4, retry_count=1, max_retries=5,
        started_at=1_800_000_000.0, ended_at=1_800_000_001.0, status_code=503,
        retryable=True, error={"message": "do not retain"}, request={"secret": "do not retain"})
    hooks["pre_api_request"](
        api_request_id=request_id, api_call_count=4, retry_count=0, max_retries=5,
        started_at=1_800_000_002.0, conversation_history=["private"])
    hooks["post_api_request"](
        api_request_id=request_id, api_call_count=4, retry_count=0, max_retries=5,
        started_at=1_800_000_002.0, ended_at=1_800_000_003.0,
        assistant_message="must not be retained")

    evidence = native_run.retry_observer_evidence(ledger)
    encoded = json.dumps(evidence)
    retained = ledger.read_text()
    assert evidence["capture_status"] == "captured"
    assert evidence["capture_completeness"] == "not_guaranteed"
    assert "fail_open" in evidence["capture_limitations"]
    assert evidence["observer_registered"] is True
    assert evidence["pre_request_count"] == 2
    assert evidence["observed_additional_attempts"] == 1
    assert evidence["events"][2]["http_status"] == 503
    assert evidence["events"][2]["retryable"] is True
    assert evidence["events"][2]["request_id"] != request_id
    assert "never retain this" not in encoded
    assert "private" not in encoded
    assert "do not retain" not in encoded
    assert "must not be retained" not in encoded
    assert "never retain this" not in retained
    assert "private" not in retained
    assert "do not retain" not in retained
    assert "must not be retained" not in retained
    assert request_id not in retained


def test_native_retry_observer_rejects_unexpected_payload_fields_and_caps_events(tmp_path, monkeypatch):
    monkeypatch.setattr(native_run, "ROOT", tmp_path)
    ledger = tmp_path / ".raw/native-api-observer.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps({"event": "observer_registered", "observed_at": 1.0,
                                  "request": "must not survive"}) + "\n")
    assert native_run.retry_observer_evidence(ledger)["capture_status"] == "invalid"

    spec = importlib.util.spec_from_file_location(
        "native_api_observer_cap_test", ROOT / "config/native-api-observer/__init__.py")
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    observer._events = 0
    monkeypatch.setattr(observer, "_ledger_path", lambda: ledger)
    ledger.write_text("")
    for _ in range(observer._MAX_EVENTS + 10):
        observer._record("observer_registered")
    assert len(ledger.read_text().splitlines()) == observer._MAX_EVENTS
    evidence = native_run.retry_observer_evidence(ledger)
    assert evidence["capture_status"] == "event_limit_reached"
    assert evidence["capture_truncated_possible"] is True
    assert evidence["event_count"] == observer._MAX_EVENTS


def test_native_trial_stages_observer_and_requires_three_registered_hooks(tmp_path):
    class AgentEnvironment:
        def __init__(self):
            self.calls = []

        async def exec(self, *, command, env, timeout_sec):
            self.calls.append((command, env, timeout_sec))
            output = "registrations: 0 tool(s), 3 hook(s)" if "plugins doctor" in command else ""
            return SimpleNamespace(return_code=0, stdout=output, stderr="")

    environment = AgentEnvironment()
    result = __import__("asyncio").run(native_trial.stage_retry_observer(
        environment, ROOT, "/tmp/hermes", enable=True, ledger_path="/logs/agent/native-api-observer.jsonl"))
    assert result == {"staged": True, "registration_smoke": True,
                      "registered_hook_count": 3, "enabled": True}
    assert "native-api-observer" in environment.calls[0][0]
    assert "plugins doctor" in environment.calls[1][0]
    assert "plugins enable" in environment.calls[2][0]
    assert environment.calls[1][1]["WPB_NATIVE_RETRY_LEDGER"] == ""
    assert environment.calls[2][1]["WPB_NATIVE_RETRY_LEDGER"].startswith("/logs/agent/")


def test_native_trial_stage_command_copies_only_reviewed_plugin_files(tmp_path):
    home = tmp_path / "hermes-home"
    command = native_trial.observer_stage_command(ROOT, str(home))
    subprocess.run(shlex.split(command), check=True, capture_output=True)
    staged = home / "plugins/native-api-observer"
    assert (staged / "plugin.yaml").read_bytes() == (
        ROOT / "config/native-api-observer/plugin.yaml").read_bytes()
    assert (staged / "__init__.py").read_bytes() == (
        ROOT / "config/native-api-observer/__init__.py").read_bytes()


def test_native_trial_refuses_retry_observer_without_registered_hook_smoke():
    class AgentEnvironment:
        def __init__(self):
            self.calls = 0

        async def exec(self, *, command, env, timeout_sec):
            self.calls += 1
            output = "registrations: 0 tool(s), 2 hook(s)" if "plugins doctor" in command else ""
            return SimpleNamespace(return_code=0, stdout=output, stderr="")

    environment = AgentEnvironment()
    with pytest.raises(RuntimeError, match="native_retry_observer_registration_failed"):
        __import__("asyncio").run(native_trial.stage_retry_observer(
            environment, ROOT, "/tmp/hermes"))
    assert environment.calls == 2


def test_challenge_verdict_sanitizer_keeps_research_completion_and_diagnostics(tmp_path, monkeypatch):
    monkeypatch.setattr(native_run, "ROOT", tmp_path)
    path = tmp_path / ".raw/verdict.json"
    write_json(path, {
        "complete": False,
        "verified_research_completion": True,
        "strict_delivery_completion": False,
        "scorer_version": "challenge-1.0.0",
        "checks": {"delivery": False, "financial_answer": True, "evidence": True, "robustness": True},
        "details": {"claims": {"margin": {"answer": True, "evidence": True, "control:scale": True}}},
        "errors": ["delivery:extra_claim"],
        "isolation": {"network_namespace_none": True, "network_probe_blocked": True,
                      "no_inference_key": True, "no_docker_socket": True},
    })

    verdict = native_run.sanitized_verdict(path)

    assert verdict["complete"] is False
    assert verdict["verified_research_completion"] is True
    assert verdict["scorer_version"] == "challenge-1.0.0"
    assert verdict["checks"]["robustness"] is True
    assert verdict["details"]["claims"]["margin"]["control:scale"] is True
    assert verdict["errors"] == ["delivery:extra_claim"]


def test_live_trials_accept_a_fork_checkout_only_with_default_branch_and_supplied_key(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("RUNNER_OS", "Linux")
    monkeypatch.setenv("GITHUB_REPOSITORY", "Maintainer/workpaperbench")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("OPENROUTER_API_KEY", "supplied-capped-key")

    native_run.validate_live_environment()
    native_trial.validate_live_environment()

    monkeypatch.setenv("GITHUB_REF", "refs/heads/feature")
    with pytest.raises(ValueError, match="default_branch_actions"):
        native_run.validate_live_environment()
    with pytest.raises(SystemExit, match="main-branch"):
        native_trial.validate_live_environment()

    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.delenv("OPENROUTER_API_KEY")
    with pytest.raises(ValueError, match="missing_openrouter_key"):
        native_run.validate_live_environment()
    with pytest.raises(SystemExit, match="supplied capped key"):
        native_trial.validate_live_environment()


def test_key_free_install_smoke_accepts_fork_repository_and_rejects_any_supplied_key(monkeypatch):
    for name in list(os.environ):
        if name.endswith("API_KEY") or name in ("GH_TOKEN", "GITHUB_TOKEN"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("RUNNER_OS", "Linux")
    monkeypatch.setenv("GITHUB_REPOSITORY", "Maintainer/workpaperbench-fork")

    check_install.validate_key_free_environment()

    monkeypatch.setenv("OPENROUTER_API_KEY", "unread-and-never-printed")
    with pytest.raises(RuntimeError, match="must be key-free"):
        check_install.validate_key_free_environment()
    monkeypatch.delenv("OPENROUTER_API_KEY")
    monkeypatch.setenv("GITHUB_REPOSITORY", "invalid/repo/path")
    with pytest.raises(RuntimeError, match="Linux GitHub Actions runner"):
        check_install.validate_key_free_environment()


def test_github_history_api_uses_runtime_repository_and_rejects_invalid_slug(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "Maintainer/workpaperbench-fork")
    calls = []

    def check_output(command, **_kwargs):
        calls.append(command)
        return b'{"workflow_runs": []}'

    monkeypatch.setattr(select_slots.subprocess, "check_output", check_output)
    assert select_slots.history("pilot", "challenge-v1-development-test") == {}
    assert "repos/Maintainer/workpaperbench-fork/actions/workflows/benchmark.yml/runs" in calls[0][-1]
    monkeypatch.setenv("GITHUB_REPOSITORY", "bad/repository/path")
    with pytest.raises(ValueError, match="invalid_github_repository"):
        select_slots.repository_path("repos/CaoimhConway/workpaperbench/actions/runs")


def test_benchmark_workflow_keeps_manual_default_branch_and_key_guards():
    workflow = (ROOT / ".github/workflows/benchmark.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert not re.search(r"(?m)^\s*(?:push|pull_request):", workflow)
    assert workflow.count("github.event_name == 'workflow_dispatch'") == 3
    assert workflow.count("github.ref == 'refs/heads/main'") == 3
    assert "OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}" in workflow
    assert 'run: test -n "$OPENROUTER_API_KEY"' in workflow
