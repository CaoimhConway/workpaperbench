"""Import immutable, screened Actions evidence and reconcile missing records."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile
from datetime import datetime, timezone

from select_slots import REPO, api, job_slots, job_started, pages, run_manifest

ROOT = Path(__file__).resolve().parent.parent
FILES = {"record.json", "answer.json", "verdict.json", "answer.raw.txt", "tool-evidence.json"}
SECRET = re.compile(rb"sk-or-v1-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")


def screened(data):
    token = os.environ.get("GH_TOKEN", "").encode()
    from native_run import credential_in
    return not credential_in(data, token.decode())


def import_archive(data, artifact, root):
    if len(data) > 2_000_000:
        raise ValueError("oversized_artifact")
    expected = artifact.get("digest")
    if expected and expected != "sha256:" + hashlib.sha256(data).hexdigest():
        raise ValueError("artifact_archive_digest_mismatch")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        groups = {}
        if len(entries) > 2 * len(FILES):
            raise ValueError("unexpected_archive_entry")
        for entry in entries:
            parts = Path(entry.filename).parts
            if entry.file_size > 200_000 or len(parts) not in (1, 2) or parts[-1] not in FILES:
                raise ValueError("unexpected_archive_entry")
            group = parts[0] if len(parts) == 2 else "single"
            if group != "single" and not re.fullmatch(r"final-wp0[1-8]-[AB]-[1-3]", group):
                raise ValueError("unexpected_archive_directory")
            if parts[-1] in groups.setdefault(group, {}):
                raise ValueError("duplicate_archive_entry")
            groups[group][parts[-1]] = archive.read(entry)
    imported = []
    for group, files in groups.items():
        if not all(screened(b) for b in files.values()):
            raise ValueError("credential_pattern_in_artifact")
        record = json.loads(files["record.json"])
        if group != "single" and record.get("slot_id") != group:
            raise ValueError("archive_slot_mismatch")
        imported.append(save_files(files, artifact, hashlib.sha256(data).hexdigest(), root))
    return imported


def save_files(files, artifact, archive_sha256, root):
    record = json.loads(files["record.json"])
    identifier = record.get("slot_id", "")
    if not re.fullmatch(r"final-wp0[1-8]-[AB]-[1-3]", identifier):
        raise ValueError("unexpected_slot")
    manifest = json.loads((root / "config/freeze.json").read_text())
    if record.get("freeze_manifest_id") != manifest["manifest_id"]:
        raise ValueError("artifact_experiment_mismatch")
    destination = root / "reports/runs" / identifier
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        target = destination / name
        if target.is_symlink() or (target.exists() and target.read_bytes() != content):
            raise ValueError("immutable_artifact_conflict")
        target.write_bytes(content)
    audit = {
        "artifact_id": artifact["id"], "archive_sha256": archive_sha256,
        "retained_file_sha256": {n: hashlib.sha256(b).hexdigest() for n, b in files.items()},
        "original_bytes_available": "answer.raw.txt" in files,
        "legacy_record_digest": record.get("answer_sha256") if "raw_sha256" not in record else None,
        "note": "Legacy answer_sha256 describes pre-normalization bytes, not the retained normalized file. No missing original is reconstructed.",
    }
    (destination / "artifact-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    return identifier


def collect(run_id, root=ROOT):
    root = Path(root)
    run = api(f"repos/{REPO}/actions/runs/{run_id}")
    manifest_id = json.loads((root / "config/freeze.json").read_text())["manifest_id"]
    if run_manifest(run, "final", {}) != manifest_id:
        raise ValueError("run_experiment_mismatch")
    imported = []
    for artifact in pages(f"repos/{REPO}/actions/runs/{run_id}/artifacts", "artifacts"):
        if not artifact["name"].startswith(("slot-", "pair-")) or artifact.get("expired"):
            continue
        data = subprocess.check_output(["gh", "api", f"repos/{REPO}/actions/artifacts/{artifact['id']}/zip"])
        imported.extend(import_archive(data, artifact, root))
    states = {}
    for job in pages(f"repos/{REPO}/actions/runs/{run_id}/jobs?filter=all", "jobs"):
        for identifier in job_slots(job):
            started = job_started(job)
            state = "running" if started and job["status"] == "in_progress" else (
                "artifact_missing" if started and job.get("conclusion") == "success" else
                "infra_failed" if started else "unstarted")
            states[identifier] = {"status": state, "run_id": run_id, "job_id": job["id"],
                "run_attempt": job.get("run_attempt", 1), "started_at": job.get("started_at"),
                "finished_at": job.get("completed_at"), "job_conclusion": job.get("conclusion")}
    result = {"run_id": run_id, "commit_sha": run["head_sha"], "manifest_id": manifest_id,
              "as_of": datetime.now(timezone.utc).isoformat(), "workflow_status": run["status"],
              "workflow_conclusion": run.get("conclusion"), "imported_slots": sorted(set(imported)),
              "slots": states}
    (root / "reports/reconciliation.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Imported", len(set(imported)), "slot artifacts. Reconciled", len(states), "scheduled job states.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", type=int, required=True)
    args = parser.parse_args()
    collect(args.run_id)
