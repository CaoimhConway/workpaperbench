"""Detached challenge scoring review validation and evidence correction tests."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fresh_replay
import challenge_evidence_review as review
import native_run
import select_slots


TASK_KEYS = review.TASK_KEYS


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _set_review_identity(bundle):
    bundle["content_hash"] = review.review_content_hash(bundle)
    bundle["review_id"] = "challenge-v1-scoring-review-" + bundle["content_hash"][:12]
    return bundle


def _fixture(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    task_map = {}
    for key in TASK_KEYS:
        task_path = f"datasets/challenge-v1/tasks/{key}"
        task_map[key] = {"task_id": "challenge-v1-" + key, "path": task_path,
                         "split": "evaluation", "source_group": "source-" + key}
        destination = root / task_path
        if key == "a02":
            shutil.copytree(ROOT / task_path, destination)
        else:
            write_json(destination / "tests/gold.json", {
                "task_id": "challenge-v1-" + key,
                "scorer_version": review.BASE_SCORER_VERSION,
                "answers": {},
            })
            shutil.copyfile(ROOT / task_path / "tests/reference.json",
                            destination / "tests/reference.json")
            shutil.copytree(ROOT / task_path / "tests/workpaperbench",
                            destination / "tests/workpaperbench")
            write_json(destination / "environment/evidence.json", [])

    for relative in review.HASH_PATHS:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)

    manifest = {
        "dataset_id": "challenge-v1",
        "stage": "final",
        "manifest_id": "challenge-v1-evaluation-0123456789ab",
        "scorer_version": review.BASE_SCORER_VERSION,
        "tasks": task_map,
    }
    manifest_path = root / review.EVALUATION_RELATIVE
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    manifest_path.write_bytes(manifest_bytes)

    bundle_tasks = {}
    for key, task in task_map.items():
        gold_path = root / task["path"] / "tests/gold.json"
        bundle_tasks[key] = {
            "task_id": task["task_id"],
            "gold_sha256": _hash(gold_path.read_bytes()),
            "additional_evidence_paths": copy.deepcopy(review.EXPECTED_ADDITIONS[key]),
        }
    bundle = _set_review_identity({
        "original_manifest_id": manifest["manifest_id"],
        "original_manifest_sha256": _hash(manifest_bytes),
        "base_scorer_version": review.BASE_SCORER_VERSION,
        "scorer_version": review.SCORER_VERSION,
        "scorer_path": review.SCORER_RELATIVE,
        "hashes": {relative: _hash((root / relative).read_bytes()) for relative in review.HASH_PATHS},
        "tasks": bundle_tasks,
    })
    bundle_path = root / review.REVIEW_RELATIVE
    write_json(bundle_path, bundle)

    def frozen_inputs(manifest_id, selected_root):
        assert manifest_id == manifest["manifest_id"]
        assert Path(selected_root) == root
        return manifest

    def context(manifest_id, selected_root):
        assert manifest_id == manifest["manifest_id"]
        assert Path(selected_root) == root
        return {"manifest": manifest, "tasks": task_map}

    slots = [{"slot_id": f"final-a02-inexpensive-{rep}", "task": "challenge-v1-a02",
              "model_key": "inexpensive", "campaign": "final", "condition": "full",
              "repetition": rep, "split": "evaluation"} for rep in (1, 2, 3)]
    slots += [{"slot_id": f"final-a02-reference-{rep}", "task": "challenge-v1-a02",
               "model_key": "reference", "campaign": "final", "condition": "full",
               "repetition": rep, "split": "evaluation"} for rep in (1, 2, 3)]
    while len(slots) < 54:
        slots.append({"slot_id": f"final-a03-inexpensive-{len(slots) % 3 + 1}",
                      "task": "challenge-v1-a03", "model_key": "inexpensive",
                      "campaign": "final", "condition": "full",
                      "repetition": len(slots) % 3 + 1, "split": "evaluation"})

    monkeypatch.setattr(native_run, "frozen_inputs", frozen_inputs)
    monkeypatch.setattr(select_slots, "campaign_context", context)
    monkeypatch.setattr(select_slots, "campaign_slots", lambda _context, _stage: slots)
    return {"root": root, "manifest": manifest, "tasks": task_map,
            "bundle_path": bundle_path, "bundle": bundle, "slots": slots}


@pytest.fixture
def review_repo(tmp_path, monkeypatch):
    return _fixture(tmp_path, monkeypatch)


def test_bundle_is_strictly_bound_and_rejects_tamper_foreign_paths_and_scorer(review_repo):
    root = review_repo["root"]
    original = review.validate_review(root)
    assert len(original["slots"]) == 54

    bundle = json.loads(review_repo["bundle_path"].read_text())
    bundle["base_scorer_version"] = "challenge-1.0.0"
    write_json(review_repo["bundle_path"], bundle)
    with pytest.raises(ValueError, match="content_hash_mismatch"):
        review.validate_review(root)

    bundle = copy.deepcopy(review_repo["bundle"])
    bundle["tasks"]["a02"]["additional_evidence_paths"] = {
        "adjusted_gross_profit": [["b02:s02", "a02:s03"]]
    }
    _set_review_identity(bundle)
    write_json(review_repo["bundle_path"], bundle)
    with pytest.raises(ValueError, match="evidence_paths_invalid"):
        review.validate_review(root)

    bundle = copy.deepcopy(review_repo["bundle"])
    write_json(review_repo["bundle_path"], bundle)
    scorer_path = root / review.SCORER_RELATIVE
    scorer_path.write_bytes(scorer_path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="input_hash_mismatch"):
        review.validate_review(root)


def test_review_task_copy_adds_only_versioned_evidence_and_leaves_source_unchanged(review_repo, tmp_path):
    root = review_repo["root"]
    validated = review.validate_review(root)
    source = root / review_repo["tasks"]["a02"]["path"]
    before_tree = review.sha256(b"".join(
        path.read_bytes() for path in sorted(source.rglob("*")) if path.is_file()))
    before_gold = (source / "tests/gold.json").read_bytes()
    copied = review.prepare_task_copy(root, "a02", validated, tmp_path / "copy-a02")
    after_tree = review.sha256(b"".join(
        path.read_bytes() for path in sorted(source.rglob("*")) if path.is_file()))
    assert before_tree == after_tree
    assert (source / "tests/gold.json").read_bytes() == before_gold
    assert copied["source_gold_sha256"] == _hash(before_gold)
    corrected = json.loads((copied["task_copy"] / "tests/gold.json").read_text())
    assert corrected["scorer_version"] == review.SCORER_VERSION
    accepted = corrected["answers"]["adjusted_gross_profit"]["evidence"]
    assert ["a02:s02", "a02:s03"] in accepted
    assert ["a02:s02", "a02:s04"] in accepted
    assert (copied["task_copy"] / "tests/workpaperbench/challenge_grading.py").read_bytes() == (
        root / review.SCORER_RELATIVE).read_bytes()


def _load_task_scorer(task_copy):
    package_name = "challenge_review_task_" + str(abs(hash(str(task_copy))))
    package = ModuleType(package_name)
    package.__path__ = [str(task_copy / "tests/workpaperbench")]
    sys.modules[package_name] = package
    module_name = package_name + ".challenge_grading"
    spec = importlib.util.spec_from_file_location(
        module_name, task_copy / "tests/workpaperbench/challenge_grading.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _grade_without_sql(task_copy, answer, monkeypatch, answer_dir):
    scorer = _load_task_scorer(task_copy)
    tests = task_copy / "tests"
    gold = json.loads((tests / "gold.json").read_text())
    reference = json.loads((tests / "reference.json").read_text())
    by_sql = {claim["sql"]: claim for claim in reference["answers"] if claim["sql"]}
    calls = []

    def mocked_replay(sql, database):
        calls.append((sql, Path(database).name))
        claim = by_sql[sql]
        if Path(database).name == "data.sqlite":
            return claim["value"]
        control = next(item for item in gold["controls"] if item["database"] == Path(database).name)
        return control["expected"][claim["id"]]

    monkeypatch.setattr(scorer, "replay", mocked_replay)
    answer_dir.mkdir(parents=True)
    (answer_dir / "answer.json").write_text(json.dumps(answer), encoding="utf-8")
    verdict = scorer.grade(answer_dir, tests)
    return verdict, calls


@pytest.mark.parametrize("evidence", [["a02:s02", "a02:s03"], ["a02:s02", "a02:s04"]])
def test_added_redundant_gaap_support_is_accepted_without_local_sql(
        review_repo, tmp_path, monkeypatch, evidence):
    validated = review.validate_review(review_repo["root"])
    copied = review.prepare_task_copy(
        review_repo["root"], "a02", validated, tmp_path / "task-copy")
    answer = json.loads((copied["task_copy"] / "tests/reference.json").read_text())
    claim = next(item for item in answer["answers"] if item["id"] == "adjusted_gross_profit")
    claim["evidence"] = evidence
    verdict, calls = _grade_without_sql(
        copied["task_copy"], answer, monkeypatch, tmp_path / "answer")
    assert verdict["scorer_version"] == review.SCORER_VERSION
    assert verdict["details"]["claims"]["adjusted_gross_profit"]["evidence"] is True
    assert verdict["complete"] is True
    assert calls


@pytest.mark.parametrize("case", ["s02_only", "unrelated_s07", "missing_revenue_denominator", "invalid_shared_s01"])
def test_review_does_not_relax_single_source_shared_or_denominator_evidence(
        review_repo, tmp_path, monkeypatch, case):
    validated = review.validate_review(review_repo["root"])
    copied = review.prepare_task_copy(
        review_repo["root"], "a02", validated, tmp_path / "task-copy")
    answer = json.loads((copied["task_copy"] / "tests/reference.json").read_text())
    if case == "s02_only":
        claim = next(item for item in answer["answers"] if item["id"] == "adjusted_gross_profit")
        claim["evidence"] = ["a02:s02"]
    elif case == "unrelated_s07":
        claim = next(item for item in answer["answers"] if item["id"] == "adjusted_gross_profit")
        claim["evidence"] = ["a02:s07"]
    elif case == "missing_revenue_denominator":
        claim = next(item for item in answer["answers"] if item["id"] == "revenue_gap")
        claim["evidence"] = ["a02:s02"]
    else:
        answer["context_evidence"] = ["a02:s01"]
    verdict, _ = _grade_without_sql(
        copied["task_copy"], answer, monkeypatch, tmp_path / "answer")
    assert verdict["checks"]["evidence"] is False
    assert verdict["complete"] is False


def test_duplicate_unsafe_submission_is_rejected_before_any_sql(review_repo, tmp_path, monkeypatch):
    validated = review.validate_review(review_repo["root"])
    copied = review.prepare_task_copy(
        review_repo["root"], "a02", validated, tmp_path / "task-copy")
    answer = json.loads((copied["task_copy"] / "tests/reference.json").read_text())
    duplicate = copy.deepcopy(answer["answers"][0])
    duplicate["sql"] = "DELETE FROM inputs"
    answer["answers"].append(duplicate)
    verdict, calls = _grade_without_sql(
        copied["task_copy"], answer, monkeypatch, tmp_path / "answer")
    assert verdict["checks"]["delivery"] is False
    assert verdict["checks"]["robustness"] is None
    assert calls == []


def test_control_references_keep_exact_source_bytes_and_paths(review_repo):
    validated = review.validate_review(review_repo["root"])
    controls = review._control_answers(review_repo["root"], validated)
    assert len(controls) == 16
    for item in controls[:9]:
        reference = review_repo["root"] / item["input_file"]
        assert item["answer_bytes"] == reference.read_bytes()


def test_controls_then_user_review_use_separate_attempt_outputs(review_repo, monkeypatch):
    root = review_repo["root"]
    run_identity = ("123456", "1", "a" * 40)
    monkeypatch.setattr(fresh_replay, "require_hosted_linux", lambda _env=None: run_identity)
    validated = review.validate_review(root)
    controls = review._control_answers(root, validated)
    answer_expectations = {}
    for item in controls:
        answer_bytes = item.get("answer_bytes")
        if answer_bytes is None:
            answer_bytes = (json.dumps(item["answer"], sort_keys=True, separators=(",", ":")) + "\n").encode()
        answer_expectations[_hash(answer_bytes)] = item["expected"]
    good = {"complete": True,
            "checks": {"delivery": True, "financial_answer": True,
                       "evidence": True, "robustness": True}}
    isolation = {key: True for key in review.ISOLATION_KEYS}

    def native_trial(_root, _task, answer, _name, _workspace):
        verdict = {"scorer_version": review.SCORER_VERSION,
                   **answer_expectations.get(_hash(answer), good),
                   "isolation": isolation}
        return json.dumps(verdict, sort_keys=True).encode(), verdict

    monkeypatch.setattr(review, "run_native_trial", native_trial)
    controls_index = review.run_controls(root, env={})
    assert controls_index.parent.name == "123456-1-controls"
    control_payload = json.loads(controls_index.read_text())
    assert control_payload["passed"] == control_payload["total"] == 16

    missing_denominator = next(item for item in controls
                               if item["name"] == "revenue-denominator-missing")
    claim = next(item for item in missing_denominator["answer"]["answers"]
                 if item["id"] == "adjusted_gross_margin")
    assert claim["evidence"] == ["a02:s03"]
    assert missing_denominator["expected"]["checks"]["evidence"] is False

    submissions = root / "submissions"
    submissions.mkdir()
    answer_path = submissions / "a02.json"
    answer_path.write_bytes((root / review_repo["tasks"]["a02"]["path"]
                             / "tests/reference.json").read_bytes())
    answer_index = review.review_user_answer(root, answer_path, "a02", env={})
    assert answer_index.parent.name == "123456-1"
    assert answer_index != controls_index


def test_retained_review_uses_authenticated_real_audit_shape(review_repo, monkeypatch):
    root = review_repo["root"]
    run_identity = ("123457", "1", "b" * 40)
    monkeypatch.setattr(fresh_replay, "require_hosted_linux", lambda _env=None: run_identity)
    slot = review_repo["slots"][0]
    answer = (root / review_repo["tasks"]["a02"]["path"]
              / "tests/reference.json").read_bytes()
    original_verdict = json.dumps({"complete": False, "checks": {}}).encode()
    record_dir = root / "reports/runs" / "retained-record"
    record_dir.mkdir(parents=True)
    (record_dir / "answer.json").write_bytes(answer)
    (record_dir / "verdict.json").write_bytes(original_verdict)
    record = {"slot_id": slot["slot_id"], "retained_sha256": _hash(answer),
              "status": "complete", "verdict": {"complete": False, "checks": {}}}
    record_bytes = (json.dumps(record, sort_keys=True) + "\n").encode()
    (record_dir / "record.json").write_bytes(record_bytes)
    audit = {
        "artifact_id": 123,
        "archive_sha256": "c" * 64,
        "workflow_run": {"id": 123457, "run_attempt": 1, "head_sha": "b" * 40},
        "archive_digest_verified": True,
        "declared_slots": [slot["slot_id"]],
        "retained_file_sha256": {
            "answer.json": _hash(answer),
            "record.json": _hash(record_bytes),
            "verdict.json": _hash(original_verdict),
        },
        "original_bytes_available": False,
    }
    (record_dir / "artifact-audit.json").write_text(json.dumps(audit), encoding="utf-8")
    slot_without_verdict = review_repo["slots"][1]
    second_dir = root / "reports/runs" / "retained-without-verdict"
    second_dir.mkdir(parents=True)
    (second_dir / "answer.json").write_bytes(answer)
    second_record = {**record, "slot_id": slot_without_verdict["slot_id"]}
    second_record_bytes = (json.dumps(second_record, sort_keys=True) + "\n").encode()
    (second_dir / "record.json").write_bytes(second_record_bytes)
    second_audit = {
        **audit,
        "declared_slots": [slot_without_verdict["slot_id"]],
        "retained_file_sha256": {
            "answer.json": _hash(answer), "record.json": _hash(second_record_bytes),
        },
    }
    (second_dir / "artifact-audit.json").write_text(json.dumps(second_audit), encoding="utf-8")
    monkeypatch.setattr(fresh_replay, "discover_records",
                        lambda *_args: [
                            (record_dir / "record.json", record, slot, audit),
                            (second_dir / "record.json", second_record, slot_without_verdict, second_audit),
                        ])
    verdict = {"scorer_version": review.SCORER_VERSION, "complete": True,
               "checks": {"delivery": True, "financial_answer": True,
                          "evidence": True, "robustness": True},
               "isolation": {key: True for key in review.ISOLATION_KEYS}}
    monkeypatch.setattr(review, "run_native_trial",
                        lambda *_args: (json.dumps(verdict).encode(), verdict))

    index_path = review.review_retained(root, env={})
    index = json.loads(index_path.read_text())
    assert index["input_source"] == "retained_artifact"
    assert index["scheduled"] == 54 and index["reviewed"] == 1
    assert len(index["missing_slots"]) == 53
    assert {item["slot_id"]: item["reason"] for item in index["missing_slots"]}[
        slot_without_verdict["slot_id"]] == "retained_verdict_unavailable"
    receipt = json.loads((root / index["receipts"][0]).read_text())
    assert receipt["input_file"] == "answer.json"
    assert receipt["prior_verdict"]["complete"] is False
    assert receipt["verdict"]["complete"] is True
