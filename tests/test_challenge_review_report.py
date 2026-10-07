"""Authenticated scoring-review imports remain separate from frozen results."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from workpaperbench.challenge_report import report_scoring_reviews


MODELS = ("inexpensive", "reference")
TASKS = ("a02", "a03", "a04", "b02", "b03", "b04", "c02", "c03", "c04")
REVIEW_ID = "challenge-v1-scoring-review-test"
MANIFEST_ID = "challenge-v1-evaluation-review-report-test"
SCORER_VERSION = "challenge-1.1.1"
RUN_ID = 987654321
RUN_ATTEMPT = 2
COMMIT_SHA = "0123456789abcdef0123456789abcdef01234567"
ISOLATION = {
    "network_namespace_none": True,
    "network_probe_blocked": True,
    "no_inference_key": True,
    "no_docker_socket": True,
}


def _json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _json_bytes(value)
    path.write_bytes(raw)
    return raw


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _build_fixture(tmp_path):
    root = tmp_path / "repo"
    task_ids = {key: "challenge-v1-" + key for key in TASKS}
    schedule = []
    for task_key in TASKS:
        for model in MODELS:
            for repetition in (1, 2, 3):
                schedule.append({
                    "slot_id": f"final-{task_key}-{model}-{repetition}",
                    "task": task_ids[task_key],
                    "model_key": model,
                    "condition": "full",
                    "repetition": repetition,
                    "split": "evaluation",
                })
    assert len(schedule) == 54

    manifest = {
        "manifest_id": MANIFEST_ID,
        "scorer_version": "challenge-1.1.0",
        "schedule": "datasets/challenge-v1/evaluation.json",
        "models": {model: {} for model in MODELS},
        "tasks": {key: {"task_id": task_ids[key]} for key in TASKS},
    }
    manifest_path = root / "datasets/challenge-v1/manifests/evaluation.json"
    manifest_bytes = _write_json(manifest_path, manifest)
    _write_json(root / manifest["schedule"], schedule)

    bundle = {
        "review_id": REVIEW_ID,
        "scorer_version": SCORER_VERSION,
        "original_manifest_id": MANIFEST_ID,
        "original_manifest_sha256": _sha(manifest_bytes),
    }
    bundle_bytes = _write_json(root / "datasets/challenge-v1/scoring-review.json", bundle)

    original_verdict = {
        "scorer_version": "challenge-1.1.0",
        "checks": {
            "financial_answer": True,
            "evidence": False,
            "robustness": True,
            "delivery": True,
        },
        "details": {
            "claims": {
                "revenue_gap": {"evidence": True},
                "adjusted_gross_profit": {"evidence": False},
                "adjusted_gross_margin": {"evidence": False},
                "margin_gap": {"evidence": False},
            },
            "conclusion": {"evidence": False},
        },
        "verified_research_completion": False,
        "strict_delivery_completion": False,
    }
    revised_verdict = {
        "scorer_version": SCORER_VERSION,
        "checks": {
            "financial_answer": True,
            "evidence": True,
            "robustness": True,
            "delivery": True,
        },
        "details": {
            "claims": {
                "revenue_gap": {"evidence": True},
                "adjusted_gross_profit": {"evidence": True},
                "adjusted_gross_margin": {"evidence": True},
                "margin_gap": {"evidence": True},
            },
            "conclusion": {"evidence": True},
        },
        "verified_research_completion": True,
        "strict_delivery_completion": True,
        "isolation": copy.deepcopy(ISOLATION),
    }

    run_dir = root / "reports/challenge-v1/scoring-reviews" / REVIEW_ID / f"{RUN_ID}-{RUN_ATTEMPT}"
    retained_slots = [
        next(slot for slot in schedule if slot["slot_id"] == f"final-a02-{model}-1")
        for model in MODELS
    ]
    receipt_paths = []
    review_hashes = {}
    originals = {}

    for slot in retained_slots:
        slot_id = slot["slot_id"]
        original_dir = root / "reports/runs" / MANIFEST_ID / slot_id
        answer = {"task_id": slot["task"], "answers": [], "conclusion": None}
        answer_bytes = _write_json(original_dir / "answer.json", answer)
        record = {
            **slot,
            "status": "completed",
            "verdict": copy.deepcopy(original_verdict),
        }
        record_bytes = _write_json(original_dir / "record.json", record)
        prior_verdict_bytes = _write_json(original_dir / "verdict.json", original_verdict)
        original_audit_bytes = _write_json(original_dir / "artifact-audit.json", {
            "archive_digest_verified": True,
            "retained_file_sha256": {
                "answer.json": _sha(answer_bytes),
                "record.json": _sha(record_bytes),
                "verdict.json": _sha(prior_verdict_bytes),
            },
        })
        originals[slot_id] = {
            "answer.json": answer_bytes,
            "record.json": record_bytes,
            "verdict.json": prior_verdict_bytes,
            "artifact-audit.json": original_audit_bytes,
        }

        slot_dir = run_dir / slot_id
        verifier_bytes = _write_json(slot_dir / "verifier.json", revised_verdict)
        verifier_path = (slot_dir / "verifier.json").relative_to(root).as_posix()
        receipt = {
            "review_id": REVIEW_ID,
            "manifest_id": MANIFEST_ID,
            "manifest_sha256": _sha(manifest_bytes),
            "scorer_version": SCORER_VERSION,
            "run_id": RUN_ID,
            "run_attempt": RUN_ATTEMPT,
            "commit_sha": COMMIT_SHA,
            "input_source": "retained_artifact",
            "review_bundle_sha256": _sha(bundle_bytes),
            "slot_id": slot_id,
            "task_id": slot["task"],
            "model_key": slot["model_key"],
            "repetition": slot["repetition"],
            "split": slot["split"],
            "input_file": "answer.json",
            "input_sha256": _sha(answer_bytes),
            "record_sha256": _sha(record_bytes),
            "artifact_audit_sha256": _sha(original_audit_bytes),
            "prior_verdict_sha256": _sha(prior_verdict_bytes),
            "prior_verdict": copy.deepcopy(original_verdict),
            "verifier_path": verifier_path,
            "verifier_bytes_sha256": _sha(verifier_bytes),
            "verdict": copy.deepcopy(revised_verdict),
            "isolation": copy.deepcopy(ISOLATION),
        }
        receipt_path = slot_dir / "receipt.json"
        receipt_bytes = _write_json(receipt_path, receipt)
        receipt_relative = receipt_path.relative_to(root).as_posix()
        receipt_paths.append(receipt_relative)
        review_hashes[verifier_path] = _sha(verifier_bytes)
        review_hashes[receipt_relative] = _sha(receipt_bytes)

    retained_ids = {slot["slot_id"] for slot in retained_slots}
    missing_slots = [
        {"slot_id": slot["slot_id"], "reason": "canonical_record_missing"}
        for slot in schedule if slot["slot_id"] not in retained_ids
    ]
    index = {
        "review_id": REVIEW_ID,
        "scorer_version": SCORER_VERSION,
        "manifest_id": MANIFEST_ID,
        "run_id": RUN_ID,
        "run_attempt": RUN_ATTEMPT,
        "commit_sha": COMMIT_SHA,
        "input_source": "retained_artifact",
        "scheduled": len(schedule),
        "reviewed": len(receipt_paths),
        "receipts": receipt_paths,
        "missing_slots": missing_slots,
    }
    index_path = run_dir / "index.json"
    index_bytes = _write_json(index_path, index)
    review_hashes[index_path.relative_to(root).as_posix()] = _sha(index_bytes)
    _write_json(run_dir / "artifact-audit.json", {
        "archive_digest_verified": True,
        "workflow_run": {
            "id": RUN_ID,
            "head_sha": COMMIT_SHA,
            "run_attempt": RUN_ATTEMPT,
        },
        "retained_file_sha256": review_hashes,
    })
    output = root / "reports/challenge-v1"
    output.mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "schedule": schedule,
        "manifest": manifest,
        "bundle": bundle,
        "run_dir": run_dir,
        "index_path": index_path,
        "originals": originals,
        "retained_slots": retained_slots,
    }


def _refresh_review_hash(fixture, relative_path):
    audit_path = fixture["run_dir"] / "artifact-audit.json"
    audit = _read_json(audit_path)
    path = fixture["root"] / relative_path
    audit["retained_file_sha256"][relative_path] = _sha(path.read_bytes())
    _write_json(audit_path, audit)


def _edit_receipt(fixture, slot_id, edit):
    receipt_path = fixture["run_dir"] / slot_id / "receipt.json"
    receipt = _read_json(receipt_path)
    edit(receipt)
    receipt_bytes = _write_json(receipt_path, receipt)
    _refresh_review_hash(fixture, receipt_path.relative_to(fixture["root"]).as_posix())
    return receipt


def _replace_new_verifier(fixture, slot_id, edit):
    slot_dir = fixture["run_dir"] / slot_id
    verifier_path = slot_dir / "verifier.json"
    verifier = _read_json(verifier_path)
    edit(verifier)
    verifier_bytes = _write_json(verifier_path, verifier)
    receipt_path = slot_dir / "receipt.json"
    receipt = _read_json(receipt_path)
    receipt["verdict"] = copy.deepcopy(verifier)
    receipt["isolation"] = copy.deepcopy(verifier["isolation"])
    receipt["verifier_bytes_sha256"] = _sha(verifier_bytes)
    _write_json(receipt_path, receipt)
    _refresh_review_hash(fixture, verifier_path.relative_to(fixture["root"]).as_posix())
    _refresh_review_hash(fixture, receipt_path.relative_to(fixture["root"]).as_posix())
    return verifier


def test_authenticated_review_corrects_only_evidence_and_keeps_54_slot_denominators(tmp_path):
    fixture = _build_fixture(tmp_path)
    before = copy.deepcopy(fixture["originals"])

    result = report_scoring_reviews(fixture["root"])
    study = result["studies"][0]
    assert study["scheduled"] == 54
    assert study["reviewed"] == 2
    assert len(study["missing_slots"]) == 52
    assert study["changed_component_slots"] == [
        "final-a02-inexpensive-1", "final-a02-reference-1"]
    assert study["changed_detail_slots"] == [
        "final-a02-inexpensive-1", "final-a02-reference-1"]
    assert result["pending_authenticated_import"] == []

    for model in MODELS:
        all_row = next(row for row in study["metrics"]
                       if row["model_key"] == model and row["scope"] == "all")
        task_row = next(row for row in study["metrics"]
                        if row["model_key"] == model and row["scope"] == "a02")
        missing_task_row = next(row for row in study["metrics"]
                                if row["model_key"] == model and row["scope"] == "a03")
        family_row = next(row for row in study["metrics"]
                          if row["model_key"] == model and row["scope"] == "family-A")
        for row in (all_row,):
            assert row["scheduled"] == 27
            assert row["verdict_coverage"] == 1
            assert row["components"]["evidence"] == {"passed": 1, "assessed": 1}
            assert row["verified_research_completion"] == 1
            assert row["strict_delivery_completion"] == 1
        assert task_row["scheduled"] == 3 and task_row["verdict_coverage"] == 1
        assert task_row["components"]["evidence"] == {"passed": 1, "assessed": 1}
        assert missing_task_row["scheduled"] == 3 and missing_task_row["verdict_coverage"] == 0
        assert missing_task_row["components"]["evidence"] == {"passed": 0, "assessed": 0}
        assert family_row["scheduled"] == 9 and family_row["verdict_coverage"] == 1
        assert study["task_macro_completion"][model] == pytest.approx(1 / 27)

    for slot_id, files in before.items():
        directory = fixture["root"] / "reports/runs" / MANIFEST_ID / slot_id
        for name, expected in files.items():
            assert (directory / name).read_bytes() == expected

    persisted = _read_json(fixture["root"] / "reports/challenge-v1/reviewed-results.json")
    assert persisted == result


def test_index_without_authenticated_archive_remains_pending(tmp_path):
    fixture = _build_fixture(tmp_path)
    audit_path = fixture["run_dir"] / "artifact-audit.json"
    audit_path.unlink()

    result = report_scoring_reviews(fixture["root"])

    assert result["studies"] == []
    assert result["pending_authenticated_import"] == [
        fixture["index_path"].relative_to(fixture["root"]).as_posix()]


@pytest.mark.parametrize("filename", ["record.json", "answer.json", "verdict.json"])
def test_tampered_original_artifacts_are_rejected(tmp_path, filename):
    fixture = _build_fixture(tmp_path)
    original_dir = (fixture["root"] / "reports/runs" / MANIFEST_ID
                    / fixture["retained_slots"][0]["slot_id"])
    path = original_dir / filename
    path.write_bytes(path.read_bytes() + b" ")

    with pytest.raises(ValueError, match="scoring_review_provenance_unverified"):
        report_scoring_reviews(fixture["root"])


def test_original_audit_hash_cannot_be_forged_to_bless_tampered_artifact(tmp_path):
    fixture = _build_fixture(tmp_path)
    original_dir = (fixture["root"] / "reports/runs" / MANIFEST_ID
                    / fixture["retained_slots"][0]["slot_id"])
    answer_path = original_dir / "answer.json"
    answer_path.write_bytes(answer_path.read_bytes() + b" ")
    audit_path = original_dir / "artifact-audit.json"
    audit = _read_json(audit_path)
    audit["retained_file_sha256"]["answer.json"] = _sha(answer_path.read_bytes())
    _write_json(audit_path, audit)

    with pytest.raises(ValueError, match="scoring_review_provenance_unverified"):
        report_scoring_reviews(fixture["root"])


def test_tampered_new_verifier_is_rejected(tmp_path):
    fixture = _build_fixture(tmp_path)
    slot_id = fixture["retained_slots"][0]["slot_id"]
    verifier_path = fixture["run_dir"] / slot_id / "verifier.json"
    verifier_path.write_bytes(verifier_path.read_bytes() + b" ")

    with pytest.raises(ValueError, match="scoring_review_provenance_unverified"):
        report_scoring_reviews(fixture["root"])


def test_tampered_new_receipt_is_rejected(tmp_path):
    fixture = _build_fixture(tmp_path)
    receipt_path = fixture["run_dir"] / fixture["retained_slots"][0]["slot_id"] / "receipt.json"
    receipt_path.write_bytes(receipt_path.read_bytes() + b" ")

    with pytest.raises(ValueError, match="scoring_review_provenance_unverified"):
        report_scoring_reviews(fixture["root"])


def test_receipt_must_bind_the_exact_original_verdict_bytes(tmp_path):
    fixture = _build_fixture(tmp_path)
    slot_id = fixture["retained_slots"][0]["slot_id"]
    _edit_receipt(fixture, slot_id,
                  lambda receipt: receipt.update(prior_verdict_sha256="0" * 64))

    with pytest.raises(ValueError, match="scoring_review_receipt_mismatch"):
        report_scoring_reviews(fixture["root"])


@pytest.mark.parametrize("identity_field", [
    "receipt_run_id", "receipt_run_attempt", "receipt_scorer",
    "receipt_manifest", "receipt_commit", "index_run_id",
])
def test_review_receipt_and_index_identity_are_bound(tmp_path, identity_field):
    fixture = _build_fixture(tmp_path)
    slot_id = fixture["retained_slots"][0]["slot_id"]
    if identity_field == "receipt_run_id":
        _edit_receipt(fixture, slot_id, lambda receipt: receipt.update(run_id=RUN_ID + 1))
    elif identity_field == "receipt_run_attempt":
        _edit_receipt(fixture, slot_id,
                      lambda receipt: receipt.update(run_attempt=RUN_ATTEMPT + 1))
    elif identity_field == "receipt_scorer":
        _edit_receipt(fixture, slot_id,
                      lambda receipt: receipt.update(scorer_version="challenge-1.1.0"))
    elif identity_field == "receipt_manifest":
        _edit_receipt(fixture, slot_id,
                      lambda receipt: receipt.update(manifest_id="different-manifest"))
    elif identity_field == "receipt_commit":
        _edit_receipt(fixture, slot_id,
                      lambda receipt: receipt.update(commit_sha="different-commit"))
    else:
        index = _read_json(fixture["index_path"])
        index["run_id"] = RUN_ID + 1
        _write_json(fixture["index_path"], index)
        _refresh_review_hash(fixture, fixture["index_path"].relative_to(fixture["root"]).as_posix())

    error = "scoring_review_identity_mismatch" if identity_field == "index_run_id" else "scoring_review_receipt_mismatch"
    with pytest.raises(ValueError, match=error):
        report_scoring_reviews(fixture["root"])


@pytest.mark.parametrize("defect", ["wrong_reviewed_count", "missing_slot_omitted"])
def test_index_reviewed_and_missing_slot_counts_must_match_receipts(tmp_path, defect):
    fixture = _build_fixture(tmp_path)
    index = _read_json(fixture["index_path"])
    if defect == "wrong_reviewed_count":
        index["reviewed"] = 1
    else:
        index["missing_slots"].pop()
    _write_json(fixture["index_path"], index)
    _refresh_review_hash(fixture, fixture["index_path"].relative_to(fixture["root"]).as_posix())

    with pytest.raises(ValueError, match="scoring_review_coverage_mismatch"):
        report_scoring_reviews(fixture["root"])


def test_only_retained_answer_filenames_are_accepted(tmp_path):
    fixture = _build_fixture(tmp_path)
    slot_id = fixture["retained_slots"][0]["slot_id"]
    _edit_receipt(fixture, slot_id, lambda receipt: receipt.update(input_file="record.json"))

    with pytest.raises(ValueError, match="scoring_review_answer_path_invalid"):
        report_scoring_reviews(fixture["root"])


def test_raw_answer_text_is_an_allowed_retained_input(tmp_path):
    fixture = _build_fixture(tmp_path)
    slot_id = fixture["retained_slots"][0]["slot_id"]
    original_dir = fixture["root"] / "reports/runs" / MANIFEST_ID / slot_id
    raw_answer = fixture["originals"][slot_id]["answer.json"]
    (original_dir / "answer.raw.txt").write_bytes(raw_answer)
    original_audit_path = original_dir / "artifact-audit.json"
    original_audit = _read_json(original_audit_path)
    original_audit["retained_file_sha256"]["answer.raw.txt"] = _sha(raw_answer)
    original_audit_bytes = _write_json(original_audit_path, original_audit)
    _edit_receipt(fixture, slot_id, lambda receipt: receipt.update(
        input_file="answer.raw.txt", input_sha256=_sha(raw_answer),
        artifact_audit_sha256=_sha(original_audit_bytes)))

    result = report_scoring_reviews(fixture["root"])

    assert result["studies"][0]["reviewed"] == 2


def test_non_evidence_scoring_changes_are_rejected_even_with_authenticated_receipt(tmp_path):
    fixture = _build_fixture(tmp_path)
    slot_id = fixture["retained_slots"][0]["slot_id"]
    _replace_new_verifier(
        fixture, slot_id,
        lambda verdict: verdict["checks"].update(financial_answer=False))

    with pytest.raises(ValueError, match="unexpected_non_evidence_scoring_change"):
        report_scoring_reviews(fixture["root"])


def test_claim_evidence_correction_can_leave_aggregate_evidence_failed(tmp_path):
    fixture = _build_fixture(tmp_path)
    slot_id = "final-a02-inexpensive-1"

    def partial_claim_correction(verdict):
        verdict["checks"]["evidence"] = False
        verdict["verified_research_completion"] = False
        verdict["strict_delivery_completion"] = False
        verdict["details"]["claims"]["adjusted_gross_profit"]["evidence"] = True
        verdict["details"]["claims"]["adjusted_gross_margin"]["evidence"] = False
        verdict["details"]["claims"]["margin_gap"]["evidence"] = False
        verdict["details"]["conclusion"]["evidence"] = False

    _replace_new_verifier(fixture, slot_id, partial_claim_correction)
    study = report_scoring_reviews(fixture["root"])["studies"][0]

    assert study["changed_component_slots"] == ["final-a02-reference-1"]
    assert study["changed_detail_slots"] == [
        "final-a02-inexpensive-1", "final-a02-reference-1"]
    row = next(row for row in study["metrics"]
               if row["scope"] == "all" and row["model_key"] == "inexpensive")
    assert row["components"]["evidence"] == {"passed": 0, "assessed": 1}
    assert row["verified_research_completion"] == 0


def test_all_required_isolation_assertions_must_be_true(tmp_path):
    fixture = _build_fixture(tmp_path)
    slot_id = fixture["retained_slots"][0]["slot_id"]
    _replace_new_verifier(
        fixture, slot_id,
        lambda verdict: verdict["isolation"].update(no_inference_key=False))

    with pytest.raises(ValueError, match="scoring_review_receipt_mismatch"):
        report_scoring_reviews(fixture["root"])


def test_review_bundle_is_bound_to_the_exact_original_manifest(tmp_path):
    fixture = _build_fixture(tmp_path)
    manifest_path = fixture["root"] / "datasets/challenge-v1/manifests/evaluation.json"
    manifest = _read_json(manifest_path)
    manifest["manifest_id"] = "different-evaluation"
    _write_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="scoring_review_origin_mismatch"):
        report_scoring_reviews(fixture["root"])
