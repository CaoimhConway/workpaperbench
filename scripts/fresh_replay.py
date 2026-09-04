"""Replay retained WorkpaperBench answers with the native verifier and no model."""
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
MAX_ANSWER = 65536
MAX_JSON = 500000
TASK_RE = re.compile(r"wp[0-9]{2}\Z")
SLOT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z")
SECRET_NAME_RE = re.compile(r"(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.IGNORECASE)


def parse_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result

    try:
        return json.loads(data, object_pairs_hook=unique,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite_json_number")))
    except RecursionError as exc:
        raise ValueError("json_depth_limit") from exc


def read_bounded(path, limit):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("unsafe_or_missing_file")
    if path.stat().st_size > limit:
        raise ValueError("file_too_large")
    data = path.read_bytes()
    if len(data) > limit:
        raise ValueError("file_too_large")
    return data


def ensure_no_symlink_ancestors(path, root):
    path = Path(path)
    lexical_root = Path(os.path.abspath(root))
    real_root = Path(root).resolve()
    lexical_path = Path(os.path.abspath(path))
    try:
        relative = lexical_path.relative_to(lexical_root)
        current = lexical_root
    except ValueError as exc:
        path = lexical_path
        try:
            relative = path.relative_to(real_root)
        except ValueError:
            raise ValueError("path_outside_repository") from exc
        current = real_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlink_path_rejected")
    if not path.resolve().is_relative_to(real_root):
        raise ValueError("path_outside_repository")
    return path.resolve()


def tree_sha256(path):
    """Hash a directory's complete file tree and reject links or special files."""
    path = Path(path)
    if path.is_symlink() or not path.is_dir():
        raise ValueError("unsafe_task_directory")
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*"), key=lambda value: value.relative_to(path).as_posix()):
        relative = item.relative_to(path).as_posix().encode("utf-8")
        if item.is_symlink():
            raise ValueError("task_tree_symlink_rejected")
        if item.is_dir():
            continue
        if not item.is_file():
            raise ValueError("task_tree_special_file_rejected")
        data = item.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def scorer_hashes(task_dir):
    root_grading = (ROOT / "workpaperbench/grading.py").read_bytes()
    root_sql = (ROOT / "workpaperbench/sql_worker.py").read_bytes()
    current = hashlib.sha256(root_grading + root_sql).hexdigest()
    task_grading = read_bounded(task_dir / "tests/workpaperbench/grading.py", 1_000_000)
    task_sql = read_bounded(task_dir / "tests/workpaperbench/sql_worker.py", 1_000_000)
    effective = hashlib.sha256(task_grading + task_sql).hexdigest()
    return current, effective


def no_secrets_in_environment(env=None):
    env = os.environ if env is None else env
    for name, value in env.items():
        if SECRET_NAME_RE.search(name) and value:
            raise ValueError("replay_secret_environment_present")


def require_hosted_linux(env=None):
    env = os.environ if env is None else env
    if env.get("GITHUB_ACTIONS") != "true" or env.get("RUNNER_OS") != "Linux":
        raise ValueError("fresh_replay_requires_hosted_linux_actions")
    no_secrets_in_environment(env)
    run_id = env.get("GITHUB_RUN_ID", "")
    attempt = env.get("GITHUB_RUN_ATTEMPT", "")
    commit = env.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[1-9][0-9]*", run_id) or not re.fullmatch(r"[1-9][0-9]*", attempt):
        raise ValueError("replay_run_identity_missing")
    if not re.fullmatch(r"[0-9a-fA-F]{40,64}", commit):
        raise ValueError("replay_commit_identity_missing")
    return run_id, attempt, commit


def clean_replay_environment(env=None):
    env = os.environ if env is None else env
    allowed = {
        "PATH", "HOME", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL",
        "GITHUB_ACTIONS", "RUNNER_OS", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT",
        "GITHUB_SHA", "GITHUB_REPOSITORY", "GITHUB_REF", "RUNNER_TEMP",
        "PYTHONUNBUFFERED", "NO_COLOR",
    }
    return {key: value for key, value in env.items() if key in allowed}


def load_real_manifest(root=ROOT):
    path = root / "datasets/real-v1/manifest.json"
    raw = read_bounded(path, MAX_JSON)
    manifest = parse_json(raw)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("manifest_id"), str):
        raise ValueError("real_manifest_identity_missing")
    from native_run import frozen_inputs
    from select_slots import campaign_context, campaign_slots
    manifest = frozen_inputs(manifest["manifest_id"], root)
    context = campaign_context(manifest["manifest_id"], root)
    campaign_slots(context, "final")
    return manifest, raw, context["tasks"]


def historical_context(root=ROOT):
    manifest_path = root / "config/freeze.json"
    raw = read_bounded(manifest_path, 1_000_000)
    manifest = parse_json(raw)
    return manifest, raw


def load_record(path):
    raw = read_bounded(path, 300_000)
    record = parse_json(raw)
    if not isinstance(record, dict):
        raise ValueError("invalid_retained_record")
    return record, raw


def validate_historical_record(root, record_path, record, record_bytes, manifest):
    if record.get("campaign") != "final" or record.get("freeze_manifest_id") != manifest.get("manifest_id"):
        raise ValueError("historical_record_experiment_mismatch")
    audit_path = record_path.parent / "artifact-audit.json"
    audit = parse_json(read_bounded(audit_path, 300_000))
    if not isinstance(audit, dict) or audit.get("archive_digest_verified") is not True:
        raise ValueError("retained_artifact_provenance_unverified")
    file_hashes = audit.get("retained_file_sha256")
    if not isinstance(file_hashes, dict) or hashlib.sha256(record_bytes).hexdigest() != file_hashes.get("record.json"):
        raise ValueError("retained_record_hash_mismatch")
    run = audit.get("workflow_run")
    if not isinstance(run, dict):
        raise ValueError("retained_workflow_identity_missing")
    if record.get("slot_id") not in audit.get("declared_slots", []):
        raise ValueError("retained_slot_not_declared")
    from collect_results import validate_record
    slot = validate_record(record, root, run)
    return slot, audit


def validate_real_record(root, record_path, record, record_bytes, manifest, tasks):
    manifest_id = manifest["manifest_id"]
    if not any(record.get(key) == manifest_id for key in ("freeze_manifest_id", "experiment_id", "manifest_id")):
        raise ValueError("real_record_experiment_mismatch")
    audit_path = record_path.parent / "artifact-audit.json"
    audit = parse_json(read_bounded(audit_path, 300_000))
    if not isinstance(audit, dict) or audit.get("archive_digest_verified") is not True:
        raise ValueError("retained_artifact_provenance_unverified")
    file_hashes = audit.get("retained_file_sha256")
    if not isinstance(file_hashes, dict) or hashlib.sha256(record_bytes).hexdigest() != file_hashes.get("record.json"):
        raise ValueError("retained_record_hash_mismatch")
    run = audit.get("workflow_run")
    run_id = record.get("run_id", record.get("github_run_id"))
    if (not isinstance(run, dict) or str(run.get("id")) != str(run_id)
            or record.get("commit_sha") != run.get("head_sha")
            or str(record.get("github_run_attempt", "")) != str(run.get("run_attempt", ""))):
        raise ValueError("retained_workflow_identity_mismatch")
    slot_id = record.get("slot_id")
    if slot_id not in audit.get("declared_slots", []):
        raise ValueError("real_record_slot_identity_mismatch")
    mode = record.get("campaign")
    from collect_results import validate_record
    slot = validate_record(record, root, run, manifest_id, mode)
    task_id = slot.get("task")
    task_key = task_id.removeprefix("real-v1-") if isinstance(task_id, str) else ""
    spec = tasks.get(task_key)
    if (not TASK_RE.fullmatch(task_key) or task_id != "real-v1-" + task_key
            or not isinstance(spec, dict) or spec.get("task_id") != task_id):
        raise ValueError("real_record_task_identity_mismatch")
    if "task_id" in record and record["task_id"] != spec["task_id"]:
        raise ValueError("real_record_task_identity_mismatch")
    return slot, audit


def retained_input(record_path, record, audit):
    file_hashes = audit["retained_file_sha256"]
    for filename in ("answer.raw.txt", "answer.json"):
        path = record_path.parent / filename
        if not path.exists() and not path.is_symlink():
            continue
        content = read_bounded(path, MAX_ANSWER)
        expected = file_hashes.get(filename)
        if not isinstance(expected, str) or hashlib.sha256(content).hexdigest() != expected:
            raise ValueError("retained_answer_hash_mismatch")
        if filename == "answer.raw.txt" and record.get("raw_sha256") and record["raw_sha256"] != expected:
            raise ValueError("retained_original_answer_hash_mismatch")
        if filename == "answer.json" and record.get("retained_sha256") and record["retained_sha256"] != expected:
            raise ValueError("retained_normalized_answer_hash_mismatch")
        return content, filename
    return None, None


def reject_credential_patterns(content):
    from native_run import credential_in
    if credential_in(content, ""):
        raise ValueError("credential_pattern_in_answer")


def previous_verdict(record_path, audit):
    path = record_path.parent / "verdict.json"
    if not path.exists() and not path.is_symlink():
        return None
    raw = read_bounded(path, 100_000)
    expected = audit.get("retained_file_sha256", {}).get("verdict.json")
    if not isinstance(expected, str) or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("retained_verdict_hash_mismatch")
    value = parse_json(raw)
    if not isinstance(value, dict):
        raise ValueError("retained_verdict_invalid")
    return {"sha256": expected, "complete": value.get("complete") is True,
            "checks": value.get("checks") if isinstance(value.get("checks"), dict) else {}}


def check_answer_identity(content, expected_task_id):
    if len(content) > MAX_ANSWER:
        raise ValueError("answer_too_large")
    answer = parse_json(content)
    if not isinstance(answer, dict) or answer.get("task_id") != expected_task_id:
        raise ValueError("answer_task_identity_mismatch")
    return answer


def user_answer(root, answer_path, task_id, dataset, tasks=None):
    if not TASK_RE.fullmatch(task_id):
        raise ValueError("invalid_task_selector")
    lexical = Path(answer_path)
    if not lexical.is_absolute():
        lexical = root / lexical
    resolved = ensure_no_symlink_ancestors(lexical, root)
    submission_root = ensure_no_symlink_ancestors(root / "submissions", root)
    if not resolved.is_relative_to(submission_root):
        raise ValueError("answer_path_must_be_under_submissions")
    if resolved.suffix.lower() != ".json":
        raise ValueError("answer_path_must_be_json")
    content = read_bounded(resolved, MAX_ANSWER)
    reject_credential_patterns(content)
    if dataset == "historical":
        task_root = ensure_no_symlink_ancestors(root / "tasks" / task_id, root)
        expected_task_id = task_id
    else:
        spec = tasks.get(task_id) if isinstance(tasks, dict) else None
        expected_path = f"datasets/real-v1/tasks/{task_id}"
        if (not isinstance(spec, dict) or spec.get("task_id") != "real-v1-" + task_id
                or spec.get("path") != expected_path):
            raise ValueError("real_task_manifest_identity_mismatch")
        task_root = ensure_no_symlink_ancestors(root / expected_path, root)
        expected_task_id = spec["task_id"]
    gold_path = ensure_no_symlink_ancestors(task_root / "tests/gold.json", root)
    gold = parse_json(read_bounded(gold_path, 300_000))
    if not isinstance(gold, dict) or gold.get("task_id") != expected_task_id:
        raise ValueError("trusted_task_identity_mismatch")
    check_answer_identity(content, expected_task_id)
    return (content, task_root, {"slot_id": "answer-" + task_id, "task": task_id},
            resolved.relative_to(Path(root).resolve()).as_posix(), None)


def run_native(root, task_dir, answer, dataset, receipt_key, run_id, attempt, commit, prior):
    task_hash = tree_sha256(task_dir)
    current_scorer, effective_scorer = scorer_hashes(task_dir)
    run_root = root / ".raw/fresh-replay" / f"{run_id}-{attempt}"
    task_copy = run_root / "tasks" / dataset / receipt_key
    trials = run_root / "trials"
    for path in (root / ".raw", root / ".raw/fresh-replay", run_root, task_copy.parent):
        if path.exists() and (path.is_symlink() or not path.is_dir()):
            raise ValueError("unsafe_replay_work_directory")
    if task_copy.exists() or task_copy.is_symlink():
        raise ValueError("replay_task_copy_already_exists")
    task_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(task_dir, task_copy)
    encoded = base64.b64encode(answer).decode("ascii")
    script = (
        "#!/bin/bash\nset -euo pipefail\n"
        "python - <<'WRITE'\nimport base64\nfrom pathlib import Path\n"
        "Path('/logs/artifacts/answer.json').write_bytes(base64.b64decode(" + repr(encoded) + "))\n"
        "WRITE\n"
    )
    solution = task_copy / "solution/solve.sh"
    solution.write_text(script)
    solution.chmod(0o755)
    trial_name = f"fresh-{dataset}-{run_id}-{attempt}-{receipt_key}"
    log_path = run_root / (trial_name + ".log")
    command = ["harbor", "trial", "start", "-p", str(task_copy), "-a", "oracle",
               "--trial-name", trial_name, "--trials-dir", str(trials)]
    env = clean_replay_environment()
    no_secrets_in_environment(env)
    with log_path.open("xb") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=600,
                       check=True, env=env, cwd=root)
    verdict_path = trials / trial_name / "verifier/verdict.json"
    verdict_bytes = read_bounded(verdict_path, 100_000)
    verdict = parse_json(verdict_bytes)
    if not isinstance(verdict, dict):
        raise ValueError("fresh_verdict_invalid")
    isolation = verdict.get("isolation")
    required = ("network_namespace_none", "network_probe_blocked", "no_inference_key", "no_docker_socket")
    if not isinstance(isolation, dict) or not all(isolation.get(key) is True for key in required):
        raise ValueError("fresh_replay_isolation_not_established")
    result = {
        "dataset": dataset,
        "slot_id": receipt_key,
        "task_sha256": task_hash,
        "scorer_sha256": current_scorer,
        "effective_task_scorer_sha256": effective_scorer,
        "input_sha256": hashlib.sha256(answer).hexdigest(),
        "prior_verdict": prior,
        "verdict_sha256": hashlib.sha256(verdict_bytes).hexdigest(),
        "verdict": verdict,
        "comparison": compare_verdict(prior, verdict),
        "run_id": run_id,
        "run_attempt": attempt,
        "commit_sha": commit,
        "scope": "Fresh native oracle replay of the exact bounded answer bytes. No model key, model call, network access, or cached replay result.",
    }
    return result


def compare_verdict(prior, current):
    if prior is None:
        return {"prior_available": False, "complete_same": None, "checks_same": None}
    current_checks = current.get("checks") if isinstance(current.get("checks"), dict) else {}
    return {
        "prior_available": True,
        "complete_same": prior["complete"] == (current.get("complete") is True),
        "checks_same": prior["checks"] == current_checks,
    }


def write_receipt(root, run_id, attempt, dataset, slot_id, receipt):
    if not SLOT_RE.fullmatch(slot_id):
        raise ValueError("unsafe_receipt_slot")
    identity = {key: receipt.get(key) for key in (
        "dataset", "manifest_id", "manifest_sha256", "slot_id", "task_id", "task_sha256",
        "scorer_sha256", "effective_task_scorer_sha256", "input_sha256", "run_id", "run_attempt",
    )}
    receipt = dict(receipt)
    receipt["receipt_identity_sha256"] = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    destination = root / "reports/fresh-replay" / f"{run_id}-{attempt}" / dataset / slot_id
    ensure_no_symlink_ancestors(destination, root)
    for parent in (root / "reports", root / "reports/fresh-replay", destination.parent, destination):
        if parent.exists() and not parent.is_dir():
            raise ValueError("unsafe_receipt_directory")
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / "receipt.json"
    data = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(target, flags, 0o644)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
    return target


def discover_records(root, dataset, manifest):
    manifest_id = manifest["manifest_id"]
    if dataset == "historical":
        paths = sorted((root / "reports/runs").glob("**/record.json"))
    else:
        paths = sorted((root / "reports/runs" / manifest_id).glob("**/record.json"))
    records = []
    for path in paths:
        ensure_no_symlink_ancestors(path, root)
        record, raw = load_record(path)
        if dataset == "historical":
            if record.get("campaign") != "final" or record.get("freeze_manifest_id") != manifest_id:
                continue
            slot, audit = validate_historical_record(root, path, record, raw, manifest)
        else:
            if not any(record.get(key) == manifest_id for key in ("freeze_manifest_id", "experiment_id", "manifest_id")):
                continue
            slot, audit = validate_real_record(root, path, record, raw, manifest, manifest.get("tasks", {}))
        records.append((path, record, slot, audit))
    return records


def selected_task(root, dataset, task_key, tasks=None):
    if not isinstance(task_key, str) or not TASK_RE.fullmatch(task_key):
        raise ValueError("invalid_task_identity")
    if dataset == "historical":
        task_dir = ensure_no_symlink_ancestors(root / "tasks" / task_key, root)
        expected_task_id = task_key
    else:
        spec = tasks.get(task_key) if isinstance(tasks, dict) else None
        expected_path = f"datasets/real-v1/tasks/{task_key}"
        if (not isinstance(spec, dict) or spec.get("task_id") != "real-v1-" + task_key
                or spec.get("path") != expected_path):
            raise ValueError("real_task_manifest_identity_mismatch")
        task_dir = ensure_no_symlink_ancestors(root / expected_path, root)
        expected_task_id = spec["task_id"]
    gold_path = ensure_no_symlink_ancestors(task_dir / "tests/gold.json", root)
    gold = parse_json(read_bounded(gold_path, 300_000))
    if not isinstance(gold, dict) or gold.get("task_id") != expected_task_id:
        raise ValueError("trusted_task_identity_mismatch")
    return task_dir, expected_task_id


def replay_selected(root, dataset, slot_filter, answer_path=None, task_key=None, env=None):
    run_id, attempt, commit = require_hosted_linux(env)
    if dataset not in {"historical", "real-v1"}:
        raise ValueError("invalid_dataset")
    if dataset == "historical":
        manifest, manifest_bytes = historical_context(root)
        tasks = None
    else:
        manifest, manifest_bytes, tasks = load_real_manifest(root)
    manifest_id = manifest.get("manifest_id")
    if not isinstance(manifest_id, str):
        raise ValueError("dataset_manifest_identity_missing")
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    receipts = []

    if answer_path:
        if not task_key:
            raise ValueError("answer_task_required")
        content, task_dir, slot, input_name, prior = user_answer(root, answer_path, task_key, dataset, tasks)
        receipt_key = slot["slot_id"]
        receipt = run_native(root, task_dir, content, dataset, receipt_key, run_id, attempt, commit, prior)
        receipt.update({"manifest_id": manifest_id, "manifest_sha256": manifest_hash,
                        "task_id": task_dir.name if dataset == "historical" else tasks[task_key]["task_id"],
                        "input_file": input_name, "input_source": "user_submission"})
        target = write_receipt(root, run_id, attempt, dataset, receipt_key, receipt)
        receipts.append(target)
        return receipts

    if not slot_filter:
        raise ValueError("slot_selector_required")
    records = discover_records(root, dataset, manifest)
    if slot_filter != "all":
        if not SLOT_RE.fullmatch(slot_filter):
            raise ValueError("invalid_slot_selector")
        records = [item for item in records if item[2].get("slot_id") == slot_filter]
        if not records:
            raise ValueError("retained_slot_not_found")
    elif not records:
        raise ValueError("no_retained_answers_found")

    for record_path, record, slot, audit in records:
        slot_id = slot.get("slot_id")
        content, filename = retained_input(record_path, record, audit)
        if content is None:
            if slot_filter == "all":
                print(slot_id + ": retained answer unavailable, skipped", file=sys.stderr)
                continue
            raise ValueError("retained_answer_unavailable")
        task_key = slot.get("task")
        if dataset == "real-v1" and isinstance(task_key, str):
            task_key = task_key.removeprefix("real-v1-")
        task_dir, expected_task_id = selected_task(root, dataset, task_key, tasks)
        gold_path = ensure_no_symlink_ancestors(task_dir / "tests/gold.json", root)
        gold = parse_json(read_bounded(gold_path, 300_000))
        if not isinstance(gold, dict) or gold.get("task_id") != expected_task_id:
            raise ValueError("trusted_task_identity_mismatch")
        reject_credential_patterns(content)
        prior = previous_verdict(record_path, audit)
        receipt = run_native(root, task_dir, content, dataset, slot_id, run_id, attempt, commit, prior)
        receipt.update({"manifest_id": manifest_id, "manifest_sha256": manifest_hash,
                        "task_id": expected_task_id, "input_file": filename,
                        "input_source": "retained_artifact",
                        "record_sha256": hashlib.sha256(record_path.read_bytes()).hexdigest()})
        receipts.append(write_receipt(root, run_id, attempt, dataset, slot_id, receipt))
    if not receipts:
        raise ValueError("no_retained_answers_available")
    return receipts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("historical", "real-v1"), required=True)
    parser.add_argument("--slot", help="Retained slot id or all")
    parser.add_argument("--answer", help="Committed answer.json below submissions/")
    parser.add_argument("--task", help="Task key such as wp03 for --answer")
    args = parser.parse_args(argv)
    if args.answer and args.slot not in (None, "all"):
        parser.error("--answer accepts only an omitted --slot or --slot all")
    try:
        receipts = replay_selected(ROOT, args.dataset, args.slot, args.answer, args.task)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        raise SystemExit("Fresh replay failed: " + (str(exc) or type(exc).__name__)) from exc
    for path in receipts:
        print("Wrote immutable receipt", path.relative_to(ROOT))
    print("Fresh replay complete for", len(receipts), "answer(s)")


if __name__ == "__main__":
    main()
