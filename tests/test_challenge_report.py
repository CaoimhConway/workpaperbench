"""Missing outcomes stay in completion denominators and provenance is required."""
import hashlib
import json

import pytest

from workpaperbench.challenge_report import failure_categories, report_challenge, select_showcase, write_showcase


def test_coverage_finance_delivery_and_receipt_integrity(tmp_path):
    base = tmp_path / "datasets/challenge-v1"
    (base / "manifests").mkdir(parents=True)
    slots = [{"slot_id": f"pilot-{key}-inexpensive-{r}", "campaign": "pilot", "task": "challenge-v1-" + key,
              "model_key": "inexpensive", "condition": "full", "repetition": r, "split": "development"}
             for key in ("a01", "b01", "c01") for r in (1, 2, 3)]
    (base / "pilot.json").write_text(json.dumps(slots))
    manifest = {"manifest_id": "challenge-test", "stage": "pilot", "schedule": "datasets/challenge-v1/pilot.json",
                "models": {"inexpensive": {}}, "tasks": {key: {"task_id": "challenge-v1-" + key} for key in ("a01", "b01", "c01")}}
    (base / "manifests/development.json").write_text(json.dumps(manifest))
    directory = tmp_path / "reports/runs/challenge-test" / slots[0]["slot_id"]
    directory.mkdir(parents=True)
    record = {**slots[0], "status": "task_failed", "verdict": {"checks": {"financial_answer": False, "evidence": True, "robustness": True, "delivery": True},
              "verified_research_completion": False, "strict_delivery_completion": False}}
    raw = json.dumps(record).encode()
    (directory / "record.json").write_bytes(raw)
    (directory / "artifact-audit.json").write_text(json.dumps({"archive_digest_verified": True, "retained_file_sha256": {"record.json": hashlib.sha256(raw).hexdigest()}}))
    study = report_challenge(tmp_path)["studies"][0]
    total = next(r for r in study["metrics"] if r["scope"] == "all")
    assert total["scheduled"] == 9 and total["verdict_coverage"] == 1
    assert total["components"]["financial_answer"] == {"passed": 0, "assessed": 1}
    assert total["components"]["delivery"] == {"passed": 1, "assessed": 1}
    assert total["verified_research_completion"] == total["strict_delivery_completion"] == 0
    assert total["unknown_cost_slots"] == 9
    assert study["task_macro_completion"]["inexpensive"] == 0
    assert study["retry_observation"]["observed_additional_attempts"] is None
    assert study["retry_observation"]["captured_registered_slots"] == 0
    (directory / "record.json").write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="provenance_unverified"):
        report_challenge(tmp_path)


def test_failure_labels_do_not_turn_unit_or_evidence_contracts_into_reasoning_claims():
    assert failure_categories({"verdict": {"errors": ["change:unit", "share:evidence"]}}) == [
        "evidence_support_or_contract", "unit_representation_or_semantics"]
    assert failure_categories({"verdict": {"errors": ["assets:control:components"]}}) == [
        "calculation_recomputation"]
    assert failure_categories(None) == ["infrastructure_or_missing_outcome"]


def test_showcase_rule_prioritizes_substance_and_same_case_without_model_preference():
    def row(identifier, task, checks, complete=False):
        return {"slot": {"slot_id": identifier, "task": task},
                "record": {"verdict": {"checks": checks, "verified_research_completion": complete}}}
    passed = {"delivery": True, "financial_answer": True, "robustness": True, "evidence": True}
    rows = [row("earlier-evidence", "a", {**passed, "evidence": False}),
            row("rejected", "a", {**passed, "delivery": False, "financial_answer": False}),
            row("failure", "b", {**passed, "robustness": False}),
            row("other-case-pass", "a", passed, True), row("same-case-pass", "b", passed, True)]
    selected = select_showcase(rows)
    assert selected["primary"]["slot"]["slot_id"] == "failure"
    assert selected["contrast"]["slot"]["slot_id"] == "same-case-pass"
    assert selected["selection_kind"] == "financial_or_robustness_failure"
    assert select_showcase(rows[:1])["selection_kind"] == "evidence_failure"
    assert select_showcase(rows[3:])["selection_kind"] == "verified_completion"
    assert select_showcase([rows[1]])["selection_kind"] == "no_delivered_outcome"


def test_showcase_renders_exact_authenticated_answer_and_rejects_changed_bytes(tmp_path):
    manifest = {"manifest_id": "challenge-test", "metrics": {"showcase_selection": "declared rule"}}
    slot = {"slot_id": "final-a02-reference-1", "task": "challenge-v1-a02", "model_key": "reference"}
    answer = {"task_id": slot["task"], "answers": [{"id": "amount", "status": "answered", "value": 5,
              "unit": "USD", "evidence": ["a02-s01"], "sql": "SELECT amount FROM disclosure"}], "conclusion": None}
    directory = tmp_path / "reports/runs/challenge-test" / slot["slot_id"]
    directory.mkdir(parents=True)
    raw = json.dumps(answer).encode()
    (directory / "answer.json").write_bytes(raw)
    (directory / "artifact-audit.json").write_text(json.dumps({"retained_file_sha256": {
        "answer.json": hashlib.sha256(raw).hexdigest()}}))
    rows = [{"slot": slot, "record": {"retained_sha256": hashlib.sha256(raw).hexdigest(),
             "verdict": {"checks": {"delivery": True, "financial_answer": True,
              "evidence": True, "robustness": True}, "verified_research_completion": True}}}]
    result = write_showcase(tmp_path, tmp_path / "reports/challenge-v1", manifest, rows)
    workpaper = (tmp_path / result["primary"]["workpaper"]).read_text()
    assert "SELECT amount FROM disclosure" in workpaper
    assert "a02-s01" in workpaper and "Saved final-a02-reference-1 workpaper" in workpaper
    assert result["contrast"] is None
    (directory / "answer.json").write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="showcase_answer_provenance_unverified"):
        write_showcase(tmp_path, tmp_path / "reports/challenge-v1", manifest, rows)
    (directory / "artifact-audit.json").write_text(json.dumps({"retained_file_sha256": {
        "answer.json": hashlib.sha256(raw + b" ").hexdigest()}}))
    with pytest.raises(ValueError, match="showcase_answer_provenance_unverified"):
        write_showcase(tmp_path, tmp_path / "reports/challenge-v1", manifest, rows)
