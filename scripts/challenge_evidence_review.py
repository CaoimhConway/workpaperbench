"""Versioned, key-free review of retained challenge-v1 answers."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
REVIEW_RELATIVE = "datasets/challenge-v1/scoring-review.json"
EVALUATION_RELATIVE = "datasets/challenge-v1/manifests/evaluation.json"
BASE_SCORER_VERSION = "challenge-1.1.0"
SCORER_VERSION = "challenge-1.1.2"
SCORER_RELATIVE = "config/scorers/challenge-1.1.2.py"
HASH_PATHS = {
    "scripts/challenge_evidence_review.py",
    "config/scorers/challenge-1.1.0.py",
    SCORER_RELATIVE,
    "workpaperbench/grading.py",
    "workpaperbench/challenge_sql_worker.py",
}
TASK_KEYS = tuple(f"{family}{number:02}" for family in "abc" for number in range(2, 5))
EXPECTED_ADDITIONS = {
    key: ({"adjusted_gross_profit": [["a02:s02", "a02:s03"],
                                      ["a02:s02", "a02:s04"]]} if key == "a02" else
          {"coverage_change_bps": [["b04:s01", "b04:s03", "b04:s04"]],
           "conclusion": [["b04:s01", "b04:s03", "b04:s04"]]} if key == "b04" else {})
    for key in TASK_KEYS
}
ISOLATION_KEYS = ("network_namespace_none", "network_probe_blocked", "no_inference_key", "no_docker_socket")
HEX_256 = re.compile(r"[0-9a-f]{64}\Z")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def review_content_hash(review):
    payload = {key: value for key, value in review.items()
               if key not in ("review_id", "content_hash")}
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8"))


def _read_repo_file(root, relative, limit=2_000_000):
    from fresh_replay import ensure_no_symlink_ancestors, read_bounded

    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("scoring_review_path_invalid")
    resolved = ensure_no_symlink_ancestors(Path(root) / path, root)
    return read_bounded(resolved, limit)


def _safe_write(path, root, content):
    from fresh_replay import ensure_no_symlink_ancestors

    path = Path(path)
    ensure_no_symlink_ancestors(path.parent, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    ensure_no_symlink_ancestors(path, root)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o644)
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)


def validate_review(root=ROOT):
    """Validate the detached review bundle against the untouched evaluation freeze."""
    root = Path(root)
    from fresh_replay import parse_json, read_bounded
    from native_run import frozen_inputs
    from select_slots import campaign_context, campaign_slots

    manifest_path = root / EVALUATION_RELATIVE
    manifest_bytes = read_bounded(manifest_path, 1_000_000)
    manifest = parse_json(manifest_bytes)
    if (not isinstance(manifest, dict)
            or manifest.get("dataset_id") != "challenge-v1"
            or manifest.get("stage") != "final"
            or manifest.get("scorer_version") != BASE_SCORER_VERSION):
        raise ValueError("scoring_review_base_manifest_invalid")
    # Recheck the original freeze strictly. Operations reviews must not make this
    # scoring correction appear to be part of the frozen experiment.
    frozen = frozen_inputs(manifest.get("manifest_id"), root)
    if frozen != manifest:
        raise ValueError("scoring_review_base_manifest_mismatch")

    context = campaign_context(manifest["manifest_id"], root)
    slots = campaign_slots(context, "final")
    if len(slots) != 54:
        raise ValueError("scoring_review_evaluation_shape_invalid")

    review_bytes = _read_repo_file(root, REVIEW_RELATIVE, 500_000)
    review = parse_json(review_bytes)
    if not isinstance(review, dict):
        raise ValueError("scoring_review_bundle_invalid")
    content_hash = review.get("content_hash")
    if (not isinstance(content_hash, str) or not HEX_256.fullmatch(content_hash)
            or review_content_hash(review) != content_hash
            or review.get("review_id") != "challenge-v1-scoring-review-" + content_hash[:12]):
        raise ValueError("scoring_review_content_hash_mismatch")
    if (review.get("original_manifest_id") != manifest["manifest_id"]
            or review.get("original_manifest_sha256") != sha256(manifest_bytes)
            or review.get("base_scorer_version") != BASE_SCORER_VERSION
            or review.get("scorer_version") != SCORER_VERSION
            or review.get("scorer_path") != SCORER_RELATIVE):
        raise ValueError("scoring_review_origin_or_scorer_mismatch")

    hashes = review.get("hashes")
    if not isinstance(hashes, dict) or set(hashes) != HASH_PATHS:
        raise ValueError("scoring_review_hash_map_invalid")
    for relative, expected in hashes.items():
        if not isinstance(expected, str) or not HEX_256.fullmatch(expected):
            raise ValueError("scoring_review_hash_invalid")
        if sha256(_read_repo_file(root, relative)) != expected:
            raise ValueError("scoring_review_input_hash_mismatch")

    base = _read_repo_file(root, "config/scorers/challenge-1.1.0.py")
    corrected = _read_repo_file(root, SCORER_RELATIVE)
    old_line = b'SCORER_VERSION = "challenge-1.1.0"'
    new_line = b'SCORER_VERSION = "challenge-1.1.2"'
    if base.count(old_line) != 1 or corrected != base.replace(old_line, new_line, 1):
        raise ValueError("scoring_review_scorer_not_version_only")

    reviewed_tasks = review.get("tasks")
    if not isinstance(reviewed_tasks, dict) or set(reviewed_tasks) != set(TASK_KEYS):
        raise ValueError("scoring_review_task_map_invalid")
    for key in TASK_KEYS:
        task = context["tasks"][key]
        spec = reviewed_tasks[key]
        if (not isinstance(spec, dict) or set(spec) != {
                "task_id", "gold_sha256", "additional_evidence_paths"}
                or spec.get("task_id") != task["task_id"]):
            raise ValueError("scoring_review_task_identity_invalid")
        gold_relative = task["path"] + "/tests/gold.json"
        gold_bytes = _read_repo_file(root, gold_relative, 300_000)
        if spec.get("gold_sha256") != sha256(gold_bytes):
            raise ValueError("scoring_review_gold_hash_mismatch")
        additions = spec.get("additional_evidence_paths")
        if additions != EXPECTED_ADDITIONS[key]:
            raise ValueError("scoring_review_evidence_paths_invalid")
    return {"review": review, "review_bytes": review_bytes,
            "manifest": manifest, "manifest_bytes": manifest_bytes,
            "context": context, "slots": slots}


def prepare_task_copy(root, task_key, validated, destination):
    """Create a disposable trusted package with only the versioned correction."""
    from fresh_replay import parse_json, read_bounded, tree_sha256

    root = Path(root)
    source = root / validated["context"]["tasks"][task_key]["path"]
    source_hash = tree_sha256(source)
    reviewed_spec = validated["review"]["tasks"][task_key]
    original_gold_path = source / "tests/gold.json"
    original_gold_bytes = read_bounded(original_gold_path, 300_000)
    if sha256(original_gold_bytes) != reviewed_spec["gold_sha256"]:
        raise ValueError("scoring_review_gold_changed")
    gold = parse_json(original_gold_bytes)
    for claim_id, options in reviewed_spec["additional_evidence_paths"].items():
        claim = (gold.get("conclusion") if claim_id == "conclusion"
                 else gold.get("answers", {}).get(claim_id))
        if not isinstance(claim, dict) or not isinstance(claim.get("evidence"), list):
            raise ValueError("scoring_review_claim_missing")
        existing = [list(option) for option in claim["evidence"]]
        for option in options:
            if option not in existing:
                existing.append(list(option))
        claim["evidence"] = existing
    gold["scorer_version"] = SCORER_VERSION

    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("scoring_review_task_copy_exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    (destination / "tests/gold.json").write_text(
        json.dumps(gold, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    module_bytes = _read_repo_file(root, SCORER_RELATIVE)
    module_path = destination / "tests/workpaperbench/challenge_grading.py"
    if not module_path.is_file() or module_path.is_symlink():
        raise ValueError("scoring_review_embedded_scorer_missing")
    module_path.write_bytes(module_bytes)
    return {
        "source_task_sha256": source_hash,
        "effective_task_sha256": tree_sha256(destination),
        "source_gold_sha256": sha256(original_gold_bytes),
        "effective_gold_sha256": sha256((destination / "tests/gold.json").read_bytes()),
        "source_task": source,
        "task_copy": destination,
    }


def _write_trial_task(task_copy, answer):
    encoded = base64.b64encode(answer).decode("ascii")
    script = (
        "#!/bin/bash\nset -euo pipefail\n"
        "python - <<'WRITE'\nimport base64\nfrom pathlib import Path\n"
        "Path('/logs/artifacts/answer.json').write_bytes(base64.b64decode(" + repr(encoded) + "))\n"
        "WRITE\n"
    )
    path = Path(task_copy) / "solution/solve.sh"
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def run_native_trial(root, task_copy, answer, trial_name, workspace):
    """Run one native oracle-only verifier trial in the hosted isolated harness."""
    from fresh_replay import clean_replay_environment, parse_json, read_bounded

    workspace = Path(workspace)
    trials = workspace / "trials"
    trials.mkdir(parents=True, exist_ok=True)
    _write_trial_task(task_copy, answer)
    log_path = workspace / (trial_name + ".log")
    command = ["harbor", "trial", "start", "-p", str(task_copy), "-a", "oracle",
               "--trial-name", trial_name, "--trials-dir", str(trials)]
    env = clean_replay_environment()
    with log_path.open("xb") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=600,
                       check=True, env=env, cwd=root)
    raw = read_bounded(trials / trial_name / "verifier/verdict.json", 100_000)
    verdict = parse_json(raw)
    if not isinstance(verdict, dict) or verdict.get("scorer_version") != SCORER_VERSION:
        raise ValueError("scoring_review_verdict_version_invalid")
    isolation = verdict.get("isolation")
    if not isinstance(isolation, dict) or not all(isolation.get(key) is True for key in ISOLATION_KEYS):
        raise ValueError("scoring_review_isolation_not_established")
    return raw, verdict


def _write_receipt(root, output_root, name, receipt, verdict_bytes):
    from fresh_replay import ensure_no_symlink_ancestors

    slot_root = output_root / name
    ensure_no_symlink_ancestors(slot_root, root)
    slot_root.mkdir(parents=True, exist_ok=False)
    raw_path = slot_root / "verifier.json"
    _safe_write(raw_path, root, verdict_bytes)
    receipt = dict(receipt)
    receipt["verifier_path"] = raw_path.relative_to(root).as_posix()
    receipt["verifier_bytes_sha256"] = sha256(verdict_bytes)
    receipt_path = slot_root / "receipt.json"
    _safe_write(receipt_path, root,
                (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8"))
    return receipt_path


def _review_one(root, validated, task_key, answer, *, name, slot, run_id, attempt, commit,
                input_source, record_path=None, audit=None, original_verifier=None,
                input_file=None, workspace=None):
    from fresh_replay import read_bounded, reject_credential_patterns

    reject_credential_patterns(answer)
    task_copy_info = prepare_task_copy(
        root, task_key, validated,
        Path(workspace) / "tasks" / name)
    task_copy = task_copy_info["task_copy"]
    trial_name = f"review-{validated['review']['content_hash'][:8]}-{run_id}-{attempt}-{name}"
    raw, new_verdict = run_native_trial(root, task_copy, answer, trial_name, workspace)
    review_scorer_hash = sha256(
        _read_repo_file(root, "workpaperbench/grading.py")
        + _read_repo_file(root, SCORER_RELATIVE)
        + _read_repo_file(root, "workpaperbench/challenge_sql_worker.py"))
    record_bytes = (read_bounded(record_path, 300_000) if record_path else None)
    audit_bytes = (read_bounded(record_path.parent / "artifact-audit.json", 300_000)
                   if record_path else None)
    if record_path and sha256(record_bytes) != audit["retained_file_sha256"].get("record.json"):
        raise ValueError("retained_record_changed_during_review")
    receipt = {
        "review_id": validated["review"]["review_id"],
        "review_content_hash": validated["review"]["content_hash"],
        "review_bundle_sha256": sha256(validated["review_bytes"]),
        "manifest_id": validated["manifest"]["manifest_id"],
        "manifest_sha256": sha256(validated["manifest_bytes"]),
        "scorer_version": SCORER_VERSION,
        "review_scorer_sha256": review_scorer_hash,
        "base_scorer_sha256": validated["review"]["hashes"]["config/scorers/challenge-1.1.0.py"],
        "task_id": validated["context"]["tasks"][task_key]["task_id"],
        "slot_id": slot.get("slot_id", name),
        "model_key": slot.get("model_key"),
        "repetition": slot.get("repetition"),
        "split": slot.get("split"),
        "input_source": input_source,
        "input_file": input_file,
        "input_sha256": sha256(answer),
        "record_path": record_path.relative_to(root).as_posix() if record_path else None,
        "record_sha256": sha256(record_bytes) if record_bytes else None,
        "artifact_audit_sha256": sha256(audit_bytes) if audit_bytes else None,
        "prior_verdict": original_verifier.get("verdict") if original_verifier else None,
        "prior_verdict_sha256": original_verifier.get("sha256") if original_verifier else None,
        "verdict": new_verdict,
        "isolation": new_verdict["isolation"],
        "source_task_sha256": task_copy_info["source_task_sha256"],
        "effective_task_sha256": task_copy_info["effective_task_sha256"],
        "source_gold_sha256": task_copy_info["source_gold_sha256"],
        "effective_gold_sha256": task_copy_info["effective_gold_sha256"],
        "run_id": run_id,
        "run_attempt": attempt,
        "commit_sha": commit,
    }
    receipt_path = _write_receipt(root, Path(validated["output_root"]), name, receipt, raw)
    return receipt_path, new_verdict, sha256(raw)


def _output_root(root, review_id, run_id, attempt):
    from fresh_replay import ensure_no_symlink_ancestors

    path = Path(root) / "reports/challenge-v1/scoring-reviews" / review_id / f"{run_id}-{attempt}"
    ensure_no_symlink_ancestors(path, root)
    path.mkdir(parents=True, exist_ok=False)
    return path


def review_retained(root=ROOT, env=None):
    from fresh_replay import (discover_records, parse_json, previous_verdict, read_bounded,
                              reject_credential_patterns, require_hosted_linux, retained_input)

    root = Path(root)
    run_id, attempt, commit = require_hosted_linux(env)
    validated = validate_review(root)
    validated["output_root"] = _output_root(root, validated["review"]["review_id"], run_id, attempt)
    from fresh_replay import ensure_no_symlink_ancestors
    workspace = root / ".raw/challenge-scoring-review" / f"{run_id}-{attempt}"
    ensure_no_symlink_ancestors(workspace, root)
    if workspace.exists() or workspace.is_symlink():
        raise ValueError("scoring_review_workspace_exists")
    workspace.mkdir(parents=True, exist_ok=False)

    schedule = validated["slots"]
    scheduled_ids = {slot["slot_id"] for slot in schedule}
    records = discover_records(root, "challenge-v1", validated["manifest"])
    by_slot = {}
    for record_path, record, slot, audit in records:
        identifier = slot.get("slot_id")
        if identifier not in scheduled_ids or identifier in by_slot:
            raise ValueError("scoring_review_record_schedule_invalid")
        by_slot[identifier] = (record_path, record, slot, audit)

    receipts, missing = [], []
    for slot in schedule:
        identifier = slot["slot_id"]
        found = by_slot.get(identifier)
        if found is None:
            missing.append({"slot_id": identifier, "reason": "canonical_record_missing"})
            continue
        record_path, record, record_slot, audit = found
        answer, filename = retained_input(record_path, record, audit)
        if answer is None:
            missing.append({"slot_id": identifier, "reason": "retained_answer_unavailable",
                            "record_status": record.get("status")})
            continue
        reject_credential_patterns(answer)
        original_verifier = previous_verdict(record_path, audit)
        if original_verifier is None:
            missing.append({"slot_id": identifier, "reason": "retained_verdict_unavailable"})
            continue
        verifier_bytes = read_bounded(record_path.parent / "verdict.json", 100_000)
        if sha256(verifier_bytes) != original_verifier["sha256"]:
            raise ValueError("retained_verdict_changed_during_review")
        original_verifier["verdict"] = parse_json(verifier_bytes)
        task_key = record_slot["task"].removeprefix("challenge-v1-")
        receipt_path, _, _ = _review_one(
            root, validated, task_key, answer, name=identifier, slot=record_slot,
            run_id=run_id, attempt=attempt, commit=commit,
            input_source="retained_artifact",
            record_path=record_path, audit=audit,
            original_verifier=original_verifier, input_file=filename, workspace=workspace)
        receipts.append(receipt_path.relative_to(root).as_posix())

    index = {
        "review_id": validated["review"]["review_id"],
        "scorer_version": SCORER_VERSION,
        "manifest_id": validated["manifest"]["manifest_id"],
        "run_id": run_id,
        "run_attempt": attempt,
        "commit_sha": commit,
        "input_source": "retained_artifact",
        "scheduled": len(schedule),
        "reviewed": len(receipts),
        "receipts": receipts,
        "missing_slots": missing,
        "scope": "Available authenticated evaluation answers only. Missing answers remain unassessed; original records and verdicts are unchanged.",
    }
    index_path = validated["output_root"] / "index.json"
    _safe_write(index_path, root,
                (json.dumps(index, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return index_path


def review_user_answer(root, answer_path, task_key, env=None):
    from fresh_replay import require_hosted_linux, user_answer
    from fresh_replay import ensure_no_symlink_ancestors

    root = Path(root)
    run_id, attempt, commit = require_hosted_linux(env)
    validated = validate_review(root)
    if task_key not in validated["context"]["tasks"]:
        raise ValueError("scoring_review_task_invalid")
    answer, _task_root, slot, input_file, _prior = user_answer(
        root, answer_path, task_key, "challenge-v1", validated["context"]["tasks"])
    output_root = _output_root(root, validated["review"]["review_id"], run_id, attempt)
    validated["output_root"] = output_root
    workspace = root / ".raw/challenge-scoring-review" / f"{run_id}-{attempt}"
    ensure_no_symlink_ancestors(workspace, root)
    if workspace.exists() or workspace.is_symlink():
        raise ValueError("scoring_review_workspace_exists")
    workspace.mkdir(parents=True, exist_ok=False)
    receipt_path, _, _ = _review_one(
        root, validated, task_key, answer, name=slot["slot_id"], slot=slot,
        run_id=run_id, attempt=attempt, commit=commit,
        input_source="user_submission", input_file=input_file, workspace=workspace)
    index = {
        "review_id": validated["review"]["review_id"],
        "scorer_version": SCORER_VERSION,
        "manifest_id": validated["manifest"]["manifest_id"],
        "run_id": run_id,
        "run_attempt": attempt,
        "commit_sha": commit,
        "input_source": "user_submission",
        "scheduled": 1,
        "reviewed": 1,
        "receipts": [receipt_path.relative_to(root).as_posix()],
        "missing_slots": [],
        "mode": "single_user_answer",
        "scope": "One submitted answer, no model call. This receipt is not a scheduled evaluation slot.",
    }
    index_path = output_root / "index.json"
    _safe_write(index_path, root,
                (json.dumps(index, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return index_path


def _control_answers(root, validated):
    from fresh_replay import parse_json, read_bounded

    controls = []
    for key in TASK_KEYS:
        task_path = root / validated["context"]["tasks"][key]["path"]
        reference_bytes = read_bounded(task_path / "tests/reference.json", 300_000)
        reference = parse_json(reference_bytes)
        if reference.get("task_id") != validated["context"]["tasks"][key]["task_id"]:
            raise ValueError("scoring_review_reference_identity_invalid")
        controls.append({"name": key + "-reference", "task_key": key,
                         "input_file": validated["context"]["tasks"][key]["path"] + "/tests/reference.json",
                         "answer": reference, "answer_bytes": reference_bytes,
                         "expected": {"complete": True,
                         "checks": {"delivery": True, "financial_answer": True,
                                    "evidence": True, "robustness": True}}})
    key = "a02"
    task_path = root / validated["context"]["tasks"][key]["path"]
    reference = parse_json(read_bounded(task_path / "tests/reference.json", 300_000))

    def with_evidence(name, claim_id, evidence):
        answer = json.loads(json.dumps(reference))
        next(claim for claim in answer["answers"] if claim["id"] == claim_id)["evidence"] = evidence
        return answer

    passed = {"complete": True,
              "checks": {"delivery": True, "financial_answer": True,
                         "evidence": True, "robustness": True}}
    evidence_failure = {"complete": False,
                        "checks": {"delivery": True, "financial_answer": True,
                                   "evidence": False, "robustness": True}}

    for suffix, paths, expected in (
        ("gross-profit-s02-s03", ["a02:s02", "a02:s03"], passed),
        ("gross-profit-s02-s04", ["a02:s02", "a02:s04"], passed),
        ("gross-profit-s02-only", ["a02:s02"], evidence_failure),
        ("gross-profit-unrelated-s07", ["a02:s07"], evidence_failure),
        ("revenue-denominator-missing", ["a02:s03"], evidence_failure),
    ):
        claim = ("adjusted_gross_margin" if suffix == "revenue-denominator-missing"
                 else "adjusted_gross_profit")
        controls.append({"name": suffix, "task_key": key,
                         "input_file": task_path.relative_to(root).as_posix() + "/tests/reference.json",
                         "answer": with_evidence(suffix, claim, paths), "expected": expected})

    answer = json.loads(json.dumps(reference))
    answer["context_evidence"] = ["a02:s01"]
    controls.append({"name": "invalid-shared-s01", "task_key": key,
                     "input_file": task_path.relative_to(root).as_posix() + "/tests/reference.json", "answer": answer,
                     "expected": evidence_failure})

    answer = json.loads(json.dumps(reference))
    duplicate = json.loads(json.dumps(answer["answers"][0]))
    duplicate["sql"] = "DELETE FROM inputs"
    answer["answers"].append(duplicate)
    controls.append({"name": "duplicate-unsafe-delivery", "task_key": key,
                     "input_file": task_path.relative_to(root).as_posix() + "/tests/reference.json", "answer": answer,
                     "expected": {"complete": False,
                                  "checks": {"delivery": False, "financial_answer": None,
                                             "evidence": None, "robustness": None}}})

    key = "b04"
    task_path = root / validated["context"]["tasks"][key]["path"]
    reference = parse_json(read_bounded(task_path / "tests/reference.json", 300_000))

    def coverage_variant(name, coverage_evidence, expected):
        answer = json.loads(json.dumps(reference))
        answer["context_evidence"] = ["b04:s05", "b04:s06"]
        coverage = next(item for item in answer["answers"] if item["id"] == "coverage_change_bps")
        coverage["evidence"] = coverage_evidence
        answer["conclusion"]["evidence"] = list(coverage_evidence)
        controls.append({"name": name, "task_key": key,
                         "input_file": task_path.relative_to(root).as_posix() + "/tests/reference.json",
                         "answer": answer, "expected": expected})

    coverage_variant("may-component-source-alternative",
                     ["b04:s01", "b04:s03", "b04:s04"], passed)
    coverage_variant("coverage-missing-may-support",
                     ["b04:s03", "b04:s04"], evidence_failure)
    coverage_variant("coverage-missing-june-aggregate",
                     ["b04:s01", "b04:s02", "b04:s04"], evidence_failure)
    return controls


def run_controls(root=ROOT, env=None):
    from fresh_replay import require_hosted_linux
    from fresh_replay import ensure_no_symlink_ancestors

    root = Path(root)
    run_id, attempt, commit = require_hosted_linux(env)
    validated = validate_review(root)
    control_attempt = attempt + "-controls"
    validated["output_root"] = _output_root(
        root, validated["review"]["review_id"], run_id, control_attempt)
    workspace = root / ".raw/challenge-scoring-review" / f"{run_id}-{control_attempt}"
    ensure_no_symlink_ancestors(workspace, root)
    if workspace.exists() or workspace.is_symlink():
        raise ValueError("scoring_review_workspace_exists")
    workspace.mkdir(parents=True, exist_ok=False)
    results = []
    for item in _control_answers(root, validated):
        key = item["task_key"]
        answer = item.get("answer_bytes")
        if answer is None:
            answer = (json.dumps(item["answer"], sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        slot = {"slot_id": "control-" + item["name"], "task": "challenge-v1-" + key,
                "model_key": None, "condition": "control", "repetition": None, "split": "evaluation"}
        receipt_path, verdict, verifier_hash = _review_one(
            root, validated, key, answer, name=slot["slot_id"], slot=slot,
            run_id=run_id, attempt=attempt, commit=commit, input_source="authored_control",
            input_file=item["input_file"], workspace=workspace)
        expected = item["expected"]
        actual = {"complete": verdict.get("complete"), "checks": verdict.get("checks")}
        passed = actual == expected
        results.append({"name": item["name"], "task_id": slot["task"],
                        "expected": expected, "actual": actual, "passed": passed,
                        "verifier_bytes_sha256": verifier_hash,
                        "receipt": receipt_path.relative_to(root).as_posix()})
    controls = {
        "review_id": validated["review"]["review_id"],
        "manifest_id": validated["manifest"]["manifest_id"],
        "scorer_version": SCORER_VERSION,
        "run_id": run_id,
        "run_attempt": attempt,
        "commit_sha": commit,
        "controls": results,
        "passed": sum(row["passed"] for row in results),
        "total": len(results),
    }
    path = validated["output_root"] / "controls.json"
    _safe_write(path, root, (json.dumps(controls, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    if controls["passed"] != controls["total"]:
        raise ValueError("scoring_review_controls_failed")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controls", action="store_true", help="Run authored references and negative verifier controls")
    parser.add_argument("--answer", help="One bounded JSON answer under submissions/")
    parser.add_argument("--task", help="Evaluation task key for --answer, such as a02")
    args = parser.parse_args(argv)
    if args.controls and (args.answer or args.task):
        parser.error("--controls cannot be combined with --answer or --task")
    if bool(args.answer) != bool(args.task):
        parser.error("--answer and --task must be supplied together")
    try:
        if args.controls:
            path = run_controls()
        elif args.answer:
            path = review_user_answer(ROOT, args.answer, args.task)
        else:
            path = review_retained()
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        raise SystemExit("Challenge scoring review failed: " + (str(exc) or type(exc).__name__)) from exc
    print("Wrote immutable challenge scoring review", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
