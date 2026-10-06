"""Import immutable, screened Actions evidence and reconcile missing records."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import zipfile
from datetime import datetime, timezone

from select_slots import REPO, SLOT_PATTERN, api, job_slots, job_started, pages, repository_path, run_manifest

ROOT = Path(__file__).resolve().parent.parent
FILES = {"record.json", "answer.json", "verdict.json", "answer.raw.txt", "tool-evidence.json"}
SECRET = re.compile(rb"sk-or-v1-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")
LEGACY_MANIFEST = "wpb-v1-92baa4a72f0e"


def retained_directory(root, manifest_id, identifier):
    from attempts import record_directory
    scoped = record_directory(manifest_id, identifier, root)
    # Published legacy evidence retains its original paths.
    return scoped.parent.parent / identifier if manifest_id == LEGACY_MANIFEST else scoped


def run_campaign(run):
    title = run.get("display_title", "")
    if title.startswith("WPB::"):
        parts = title.split("::")
        if len(parts) == 3 and parts[2] in ("pilot", "final"):
            return parts[2]
    return "final"


def authenticate_attempt(artifact, run, manifest_id, cache, mode="final"):
    slot = rf"(?:{SLOT_PATTERN})"
    prefixes = (f"slot-{run['head_sha']}-{mode}-{run['id']}-",
                f"pair-{manifest_id}-{run['id']}-", f"provider-{run['head_sha']}-{run['id']}-")
    endings = (rf"([1-9][0-9]*)-({slot})", rf"([1-9][0-9]*)-({slot}(?:--{slot})?)", r"([1-9][0-9]*)")
    match = next((m for p, e in zip(prefixes, endings)
                  if (m := re.fullmatch(re.escape(p) + e, artifact['name']))), None)
    if match is None:
        raise ValueError('artifact_attempt_name_mismatch')
    attempt = int(match[1])
    if attempt not in cache:
        cache[attempt] = run if attempt == run['run_attempt'] else api(
            f"repos/{REPO}/actions/runs/{run['id']}/attempts/{attempt}")
    actual = cache[attempt]
    if (actual['id'] != run['id'] or actual['head_sha'] != run['head_sha']
            or actual['run_attempt'] != attempt):
        raise ValueError('artifact_attempt_identity_mismatch')
    artifact['workflow_run'] = {**artifact['workflow_run'], 'run_attempt': attempt}
    artifact['declared_slots'] = match[2].split('--') if match.lastindex == 2 else []
    artifact['manifest_id'] = manifest_id
    artifact['campaign'] = mode


def screened(data):
    token = os.environ.get("GH_TOKEN", "").encode()
    from native_run import credential_in
    return not credential_in(data, token.decode())


def import_archive(data, artifact, root):
    if len(data) > 2_000_000:
        raise ValueError("oversized_artifact")
    expected = artifact.get("digest")
    if expected != "sha256:" + hashlib.sha256(data).hexdigest():
        raise ValueError("artifact_archive_digest_mismatch")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        groups = {}
        campaign = artifact.get("campaign", "final")
        if len(entries) > 2 * len(FILES) or sum(e.file_size for e in entries) > 1_000_000:
            raise ValueError("unexpected_archive_entry")
        for entry in entries:
            parts = Path(entry.filename).parts
            mode = stat.S_IFMT(entry.external_attr >> 16)
            if (mode not in (0, stat.S_IFREG) or entry.is_dir() or entry.flag_bits & 1
                    or Path(entry.filename).is_absolute() or ".." in parts
                    or entry.file_size > 500_000 or len(parts) not in (1, 2) or parts[-1] not in FILES):
                raise ValueError("unexpected_archive_entry")
            group = parts[0] if len(parts) == 2 else "single"
            if group != "single" and not re.fullmatch(SLOT_PATTERN, group):
                raise ValueError("unexpected_archive_directory")
            if parts[-1] in groups.setdefault(group, {}):
                raise ValueError("duplicate_archive_entry")
            groups[group][parts[-1]] = archive.read(entry)
    prepared = []
    identifiers = set()
    for group, files in groups.items():
        if not all(screened(b) for b in files.values()):
            raise ValueError("credential_pattern_in_artifact")
        if 'record.json' not in files:
            raise ValueError('artifact_record_missing')
        record = json.loads(files["record.json"])
        if not isinstance(record, dict) or record.get('slot_id') not in artifact.get('declared_slots', []):
            raise ValueError('artifact_declared_slot_identity_mismatch')
        if group != "single" and record.get("slot_id") != group:
            raise ValueError("archive_slot_mismatch")
        if record['slot_id'] in identifiers:
            raise ValueError('duplicate_archive_slot')
        identifiers.add(record['slot_id'])
        prepared.append((files, validate_files(files, artifact, root)))
    return [save_files(files, artifact, hashlib.sha256(data).hexdigest(), destination, record)
            for files, (destination, record) in prepared]


def validate_files(files, artifact, root):
    record = json.loads(files["record.json"])
    manifest_id = artifact.get("manifest_id")
    if not manifest_id:
        manifest_id = json.loads((Path(root) / "config/freeze.json").read_text())["manifest_id"]
    mode = artifact.get("campaign", "final")
    validate_record(record, root, artifact["workflow_run"], manifest_id, mode)
    identifier = record.get("slot_id", "")
    if not re.fullmatch(SLOT_PATTERN, identifier):
        raise ValueError("unexpected_slot")
    from select_slots import campaign_context
    context = campaign_context(manifest_id, root)
    manifest = context["manifest"]
    if mode == "final" and record.get("freeze_manifest_id") != manifest["manifest_id"]:
        raise ValueError("artifact_experiment_mismatch")
    if context["dataset_id"] and record.get("dataset_manifest_id") != manifest["manifest_id"]:
        raise ValueError("artifact_dataset_mismatch")
    if record.get("experiment_id") not in (None, manifest_id):
        raise ValueError("artifact_experiment_mismatch")
    destination = retained_directory(root, manifest_id, identifier)
    if any(p.is_symlink() for p in (destination, *destination.parents) if p != root and p.is_relative_to(root)):
        raise ValueError("unsafe_artifact_destination")
    for name, content in files.items():
        target = destination / name
        if target.is_symlink() or (target.exists() and target.read_bytes() != content):
            raise ValueError("immutable_artifact_conflict")
    if "answer.raw.txt" in files and hashlib.sha256(files["answer.raw.txt"]).hexdigest() != record.get("raw_sha256"):
        raise ValueError("original_bytes_hash_mismatch")
    if "retained_sha256" in record and ("answer.json" not in files or hashlib.sha256(files["answer.json"]).hexdigest() != record["retained_sha256"]):
        raise ValueError("normalized_bytes_hash_mismatch")
    return destination, record


def save_files(files, artifact, archive_sha256, destination, record):
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        target = destination / name
        target.write_bytes(content)
    audit = {
        "artifact_id": artifact["id"], "archive_sha256": archive_sha256,
        "workflow_run": artifact["workflow_run"], "archive_digest_verified": True,
        "declared_slots": artifact['declared_slots'],
        "retained_file_sha256": {n: hashlib.sha256(b).hexdigest() for n, b in files.items()},
        "original_bytes_available": "answer.raw.txt" in files,
        "legacy_record_digest": record.get("answer_sha256") if "raw_sha256" not in record else None,
        "note": "Legacy answer_sha256 describes pre-normalization bytes, not the retained normalized file. No missing original is reconstructed.",
    }
    (destination / "artifact-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    return record['slot_id']


def validate_record(record, root, run, manifest_id=None, mode="final"):
    if not isinstance(record, dict):
        raise ValueError('invalid_artifact_record')
    from select_slots import campaign_context, campaign_slots
    if manifest_id is None:
        manifest_id = json.loads((Path(root) / "config/freeze.json").read_text())["manifest_id"]
    context = campaign_context(manifest_id, root)
    schedule = campaign_slots(context, mode)
    slots = {s["slot_id"]: s for s in schedule}
    slot = slots.get(record.get("slot_id"))
    if slot is None or any(record.get(k) != value for k, value in slot.items()):
        raise ValueError("artifact_slot_identity_mismatch")
    if record.get("experiment_id") not in (None, manifest_id):
        raise ValueError("artifact_experiment_identity_mismatch")
    if mode == "final" and record.get("freeze_manifest_id") != context["manifest"]["manifest_id"]:
        raise ValueError("artifact_freeze_identity_mismatch")
    if context["dataset_id"] and record.get("dataset_manifest_id") != context["manifest"]["manifest_id"]:
        raise ValueError("artifact_dataset_identity_mismatch")
    if context["dataset_id"] == "challenge-v1":
        task_key = slot["task"].removeprefix("challenge-v1-")
        task = context["tasks"][task_key]
        model = context["manifest"]["models"][slot["model_key"]]
        expected = {
            "experiment_id": manifest_id,
            "dataset_id": "challenge-v1",
            "dataset_manifest_id": manifest_id,
            "source_group": task["source_group"],
            "task_origin": task.get("origin"),
            "model": model["id"],
            "model_route_policy": model["route_policy"],
            "model_provider": model["provider"],
            "model_harbor_model": model["harbor_model"],
            "reservation_usd_per_slot": float(model["reservation_usd_per_slot"]),
        }
        if any(record.get(key) != value for key, value in expected.items()):
            raise ValueError("artifact_challenge_provenance_mismatch")
    if str(record.get("run_id")) != str(run["id"]) or record.get("commit_sha") != run["head_sha"]:
        raise ValueError("artifact_run_identity_mismatch")
    if str(record.get("github_run_attempt", "")) != str(run.get('run_attempt', '')) or not run.get('run_attempt'):
        raise ValueError("artifact_run_attempt_identity_mismatch")
    return slot


def missing_state(job):
    if not job_started(job):
        return "never_started"
    if job["status"] != "completed":
        return "running"
    if job.get("conclusion") == "cancelled":
        return "cancelled_exposure_unknown"
    if job.get("conclusion") == "success":
        return "completed_evidence_unavailable"
    live = [s for s in job.get("steps", []) if "native live" in s.get("name", "").lower()
            or "fresh native trials" in s.get("name", "").lower()]
    if live and all(not s.get("started_at") or s.get("conclusion") == "skipped" for s in live):
        return "setup_failed"
    return "started_exposure_unknown"


def reconciliation_path(root, context, mode):
    if mode not in ("pilot", "final"):
        raise ValueError("invalid_reconciliation_campaign")
    reports = Path(root) / "reports"
    if context["dataset_id"] == "real-v1":
        return reports / "real-v1" / (mode + "-reconciliation.json")
    if context["dataset_id"] == "challenge-v1":
        return reports / "challenge-v1" / (mode + "-reconciliation.json")
    return reports / "reconciliation.json"


def provider_archive(data, artifact, run, root):
    if len(data) > 100_000 or artifact.get("digest") != "sha256:" + hashlib.sha256(data).hexdigest():
        raise ValueError("provider_archive_digest_mismatch")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        entries = z.infolist()
        if len(entries) != 1 or entries[0].filename != "provider.json" or entries[0].file_size > 10000:
            raise ValueError("unexpected_provider_entry")
        content = z.read(entries[0])
    if not screened(content):
        raise ValueError("credential_pattern_in_provider")
    value = json.loads(content)
    if str(value.get("run_id")) != str(run["id"]):
        raise ValueError("provider_run_mismatch")
    reports = Path(root) / "reports"
    manifest_id = artifact.get("manifest_id")
    if manifest_id:
        from select_slots import campaign_context
        dataset_id = campaign_context(manifest_id, root)["dataset_id"]
        if dataset_id in ("real-v1", "challenge-v1"):
            reports = reports / dataset_id
    target = reports / "provider" / (str(run["id"]) + ".json")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != content:
        raise ValueError("immutable_provider_conflict")
    target.write_bytes(content)
    return {"artifact_id": artifact["id"], "archive_sha256": hashlib.sha256(data).hexdigest(),
            "retained_sha256": hashlib.sha256(content).hexdigest(), "workflow_run": artifact["workflow_run"]}


def collect(run_id, root=ROOT):
    root = Path(root)
    run = api(f"repos/{REPO}/actions/runs/{run_id}")
    mode = run_campaign(run)
    manifest_id = run_manifest(run, mode, {})
    if manifest_id == "development-v1" or not manifest_id:
        raise ValueError("run_experiment_mismatch")
    from select_slots import campaign_context
    context = campaign_context(manifest_id, root)
    imported, withheld, provider, attempts = [], [], None, {}
    for artifact in pages(f"repos/{REPO}/actions/runs/{run_id}/artifacts", "artifacts"):
        if not artifact["name"].startswith(("slot-", "pair-", "provider-")) or artifact.get("expired"):
            continue
        provenance = artifact.get("workflow_run", {})
        if provenance.get("id") != run_id or provenance.get("head_sha") != run["head_sha"]:
            raise ValueError("artifact_workflow_origin_mismatch")
        if artifact.get("size_in_bytes", 2_000_001) > 2_000_000:
            raise ValueError("oversized_artifact")
        data = subprocess.check_output(["gh", "api", repository_path(
            f"repos/{REPO}/actions/artifacts/{artifact['id']}/zip")])
        try:
            authenticate_attempt(artifact, run, manifest_id, attempts, mode)
            if artifact["name"].startswith("provider-"):
                provider = provider_archive(data, artifact, run, root)
            else:
                imported.extend(import_archive(data, artifact, root))
        except ValueError as exc:
            if "immutable" in str(exc):
                raise
            withheld.append({"artifact_id": artifact["id"], "reason": type(exc).__name__ + ":" + str(exc)})
    states = {}
    for job in pages(f"repos/{REPO}/actions/runs/{run_id}/jobs?filter=all", "jobs"):
        for identifier in job_slots(job):
            if not identifier.startswith(mode + "-"):
                continue
            state = missing_state(job)
            retained = retained_directory(root, manifest_id, identifier) / 'record.json'
            if identifier in imported and retained.is_file():
                state = json.loads(retained.read_text())['status']
            states[identifier] = {"status": state, "run_id": run_id, "job_id": job["id"],
                "artifact_available": identifier in imported,
                "run_attempt": job.get("run_attempt", 1), "started_at": job.get("started_at"),
                "finished_at": job.get("completed_at"), "job_conclusion": job.get("conclusion")}
    result = {"run_id": run_id, "commit_sha": run["head_sha"], "manifest_id": manifest_id,
              "as_of": datetime.now(timezone.utc).isoformat(), "workflow_status": run["status"],
              "workflow_conclusion": run.get("conclusion"), "imported_slots": sorted(set(imported)),
              "slots": states, "withheld_artifacts": withheld, "provider_artifact": provider}
    target = reconciliation_path(root, context, mode)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print("Imported", len(set(imported)), "slot artifacts. Reconciled", len(states), "scheduled job states.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", type=int, required=True)
    args = parser.parse_args()
    collect(args.run_id)
