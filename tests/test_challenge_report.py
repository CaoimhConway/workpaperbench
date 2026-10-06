"""Missing outcomes stay in completion denominators and provenance is required."""
import hashlib
import json

import pytest

from workpaperbench.challenge_report import report_challenge


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
    (directory / "record.json").write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="provenance_unverified"):
        report_challenge(tmp_path)
