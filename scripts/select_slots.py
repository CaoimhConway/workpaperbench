"""Select experiment-scoped slots without repeating an attempted execution."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent
REPO = "CaoimhConway/workpaperbench"
SLOT_PATTERN = r"(?:pilot-wp0[1-8]-[AB]-[1-9]|final-wp0[1-8]-[AB]-[1-3])"
REAL_DATASET_ID = "real-v1"
REAL_PILOT_MANIFEST_ID = "real-v1-development"


def manifest_content_hash(manifest):
    """Hash every manifest field except the hash and identifier derived from it."""
    if not isinstance(manifest, dict):
        raise ValueError("dataset_manifest_invalid")
    payload = {key: value for key, value in manifest.items()
               if key not in ("manifest_id", "content_hash")}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _repo_file(root, value, fallback=None):
    """Resolve a repository-relative manifest path without following symlinks."""
    if value is None:
        value = fallback
    if not isinstance(value, str) or not value:
        raise ValueError("dataset_input_path_missing")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("unsafe_dataset_path")
    path = Path(root)
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("dataset_input_symlink")
    if not path.is_file():
        raise ValueError("dataset_input_missing")
    return path


def _repo_directory(root, value):
    if not isinstance(value, str) or not value:
        raise ValueError("dataset_task_path_missing")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("unsafe_dataset_path")
    path = Path(root)
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("dataset_task_path_symlink")
    if not path.is_dir():
        raise ValueError("dataset_task_path_invalid")
    return path


def real_dataset_context(manifest_id, root=None):
    """Return the selected real-v1 files and task metadata, if this is that campaign."""
    root = ROOT if root is None else Path(root)
    manifest_path = root / "datasets/real-v1/manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text())
    if not isinstance(manifest, dict) or manifest.get("dataset_id") != REAL_DATASET_ID:
        raise ValueError("dataset_identity_mismatch")
    if manifest_id not in (manifest.get("manifest_id"), REAL_PILOT_MANIFEST_ID):
        return None
    if not re.fullmatch(r"real-v1-[0-9a-f]{12,64}", str(manifest.get("manifest_id", ""))):
        raise ValueError("dataset_manifest_identifier_invalid")
    content_hash = manifest.get("content_hash")
    if (not isinstance(content_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", content_hash)
            or manifest_content_hash(manifest) != content_hash):
        raise ValueError("dataset_content_hash_mismatch")
    if manifest["manifest_id"] != "real-v1-" + content_hash[:12]:
        raise ValueError("dataset_manifest_id_mismatch")
    schedule_path = _repo_file(root, manifest.get("schedule"), "datasets/real-v1/schedule.json")
    pilot_path = _repo_file(root, manifest.get("pilot"), "datasets/real-v1/pilot.json")
    schema_path = _repo_file(root, manifest.get("schema"), "datasets/real-v1/schema.json")
    tasks = manifest.get("tasks")
    groups = manifest.get("source_groups")
    if not isinstance(tasks, dict) or set(tasks) != {f"wp{i:02}" for i in range(1, 9)}:
        raise ValueError("dataset_task_map_invalid")
    if not isinstance(groups, dict) or set(groups) != set(tasks):
        raise ValueError("dataset_source_groups_invalid")
    group_splits = {"development": set(), "evaluation": set()}
    for task_key, task in tasks.items():
        expected_id = "real-v1-" + task_key
        if (not isinstance(task, dict) or task.get("task_id") != expected_id
                or task.get("split") not in group_splits
                or not isinstance(task.get("source_group"), str)
                or not task.get("source_group")
                or groups.get(task_key) != task.get("source_group")):
            raise ValueError("dataset_task_identity_invalid")
        expected_path = "datasets/real-v1/tasks/" + task_key
        if task.get("path") != expected_path:
            raise ValueError("dataset_task_path_mismatch")
        _repo_directory(root, expected_path)
        gold_path = _repo_file(root, expected_path + "/tests/gold.json")
        instruction_path = _repo_file(root, expected_path + "/instruction.md")
        gold = json.loads(gold_path.read_text())
        instruction = instruction_path.read_text()
        if (not isinstance(gold, dict) or gold.get("task_id") != expected_id
                or not re.search(rf"(?m)^Task identifier: {re.escape(expected_id)}\.", instruction)):
            raise ValueError("dataset_task_package_identity_mismatch")
        group_splits[task["split"]].add(task["source_group"])
    if group_splits["development"] & group_splits["evaluation"]:
        raise ValueError("dataset_source_group_cross_split")
    return {
        "dataset_id": REAL_DATASET_ID,
        "manifest_id": manifest["manifest_id"],
        "selected_manifest_id": manifest_id,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "schedule_path": schedule_path,
        "pilot_path": pilot_path,
        "schema_path": schema_path,
        "tasks": tasks,
        "root": root,
    }


def campaign_context(manifest_id, root=None):
    """Resolve a manifest id to its dataset without changing the legacy frozen files."""
    root = ROOT if root is None else Path(root)
    context = real_dataset_context(manifest_id, root)
    if context is not None:
        return context
    root = Path(root)
    freeze_path = root / "config/freeze.json"
    manifest = json.loads(freeze_path.read_text())
    if manifest.get("manifest_id") != manifest_id:
        raise ValueError("manifest_mismatch")
    return {
        "dataset_id": None,
        "manifest_id": manifest_id,
        "selected_manifest_id": manifest_id,
        "manifest": manifest,
        "manifest_path": freeze_path,
        "schedule_path": root / "config/schedule.json",
        "pilot_path": root / "config/pilot.json",
        "schema_path": root / "config/schema.json",
        "tasks": None,
        "root": root,
    }


def campaign_slots(context, mode):
    """Load and bind one campaign's slots to the manifest's declared task split."""
    path = context["schedule_path"] if mode == "final" else context["pilot_path"]
    slots = json.loads(path.read_text())
    if isinstance(slots, dict):
        slots = slots.get("slots")
    if not isinstance(slots, list) or not all(isinstance(slot, dict) for slot in slots):
        raise ValueError("invalid_slot_manifest")
    if context["dataset_id"] is None:
        return slots
    if mode not in ("pilot", "final"):
        raise ValueError("invalid_campaign")
    if mode == "final" and len(slots) != 48:
        raise ValueError("real_schedule_must_have_48_slots")
    if mode == "pilot" and len(slots) > 6:
        raise ValueError("real_pilot_ceiling")
    seen = set()
    task_map = context["tasks"]
    for slot in slots:
        identifier = slot.get("slot_id")
        task_id = slot.get("task")
        if (not isinstance(identifier, str) or not re.fullmatch(SLOT_PATTERN, identifier)
                or identifier in seen or slot.get("campaign") != mode):
            raise ValueError("real_slot_identity_invalid")
        seen.add(identifier)
        match = re.fullmatch(r"(?:pilot|final)-(wp0[1-8])-([AB])-([1-3])", identifier)
        task = task_map.get(task_id.removeprefix("real-v1-")) if isinstance(task_id, str) else None
        if (match is None or task is None or task.get("task_id") != task_id
                or match[1] != task_id.removeprefix("real-v1-")
                or match[2] != slot.get("arm")
                or isinstance(slot.get("repetition"), bool)
                or not isinstance(slot.get("repetition"), int)
                or int(match[3]) != slot.get("repetition")
                or slot.get("split") != task.get("split")):
            raise ValueError("real_slot_task_split_mismatch")
        if mode == "pilot" and task.get("split") != "development":
            raise ValueError("real_pilot_must_use_development_tasks")
    if mode == "pilot" and any(
            s["task"] not in {"real-v1-wp01", "real-v1-wp02", "real-v1-wp05"} for s in slots):
        raise ValueError("real_pilot_task_not_allowed")
    return slots


def api(path):
    for attempt in range(3):
        try:
            response = subprocess.check_output(["gh", "api", "--method", "GET", path],
                                               stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as error:
            status = re.search(rb'\bHTTP (\d{3})\b', error.stderr or b'')
            if attempt == 2 or status is None or status[1] not in (b'500', b'502', b'503', b'504'):
                raise
            time.sleep(attempt + 1)
        else:
            return json.loads(response)


def pages(path, key):
    for page in range(1, 101):
        response = api(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}")
        items = response[key]
        yield from items
        if len(items) < 100:
            return
    raise ValueError("history_pagination_limit")


def job_started(job):
    if job.get("status") == "queued" or job.get("conclusion") == "skipped":
        return False
    if job.get("runner_id") or any(step.get("started_at") for step in job.get("steps", [])):
        return True
    return job.get("status") == "in_progress" or (
        job.get("conclusion") == "failure" and bool(job.get("started_at")))


def run_manifest(run, mode, cache):
    """Named new runs and commit-pinned manifests for legacy runs."""
    title = run.get("display_title", "")
    if title.startswith("WPB::"):
        parts = title.split("::")
        return parts[1] if len(parts) == 3 and parts[2] == mode else None
    if mode == "pilot":
        return "development-v1"
    sha = run.get("head_sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("history_commit_missing")
    if sha not in cache:
        blob = api(f"repos/{REPO}/contents/config/freeze.json?ref={sha}")
        cache[sha] = json.loads(base64.b64decode(blob["content"]))["manifest_id"]
    return cache[sha]


def job_slots(job):
    name = job.get("name", "")
    if name.startswith("trial-") or name.startswith("pair-"):
        return re.findall(SLOT_PATTERN, name)
    return []


def history(mode, manifest_id):
    attempted, cache = {}, {}
    current = int(os.environ.get("GITHUB_RUN_ID", "0"))
    attempt = int(os.environ.get("GITHUB_RUN_ATTEMPT", "1"))
    for run in pages(f"repos/{REPO}/actions/workflows/benchmark.yml/runs", "workflow_runs"):
        named = run.get('display_title', '').startswith('WPB::')
        if named and run_manifest(run, mode, cache) != manifest_id:
            continue
        # Legacy workflow definitions only read the historical config freeze.
        if not named and manifest_id.startswith('real-v1'):
            continue
        jobs = list(pages(f"repos/{REPO}/actions/runs/{run['id']}/jobs?filter=all", "jobs"))
        jobs = [job for job in jobs if any(s.startswith(mode + "-") for s in job_slots(job))]
        if not jobs or (not named and run_manifest(run, mode, cache) != manifest_id):
            continue
        for job in jobs:
            # Exclude this invocation only, never older attempts of the same run.
            if run["id"] == current and job.get("run_attempt", 1) == attempt:
                continue
            if not job_started(job):
                continue
            for slot_id in job_slots(job):
                value = {"run_id": run["id"], "job_id": job["id"],
                         "run_attempt": job.get("run_attempt", 1),
                         "conclusion": job.get("conclusion"), "status": job["status"],
                         "started_at": job.get("started_at"), "finished_at": job.get("completed_at")}
                previous = attempted.get(slot_id)
                if previous is None or (str(value["started_at"]), value["run_id"]) < (str(previous["started_at"]), previous["run_id"]):
                    attempted[slot_id] = value
    return attempted


def selection(mode, manifest_id, batch):
    context = real_dataset_context(manifest_id)
    if context is not None:
        if mode == "pilot" and manifest_id != REAL_PILOT_MANIFEST_ID:
            raise ValueError("pilot_manifest_mismatch")
        if mode == "final" and manifest_id != context["manifest_id"]:
            raise ValueError("final_manifest_mismatch")
        slots = campaign_slots(context, mode)
        if mode == "pilot":
            slots = [s for s in slots if batch == "all" or (s["arm"] == "A" if batch == "baseline" else s["arm"] == "B")]
    elif mode == "final":
        manifest = json.loads((ROOT / "config/freeze.json").read_text())
        if manifest_id != manifest["manifest_id"]:
            raise ValueError("manifest_mismatch")
        slots = json.loads((ROOT / "config/schedule.json").read_text())
    else:
        if manifest_id != "development-v1":
            raise ValueError("pilot_manifest_mismatch")
        slots = json.loads((ROOT / "config/pilot.json").read_text())
        if len(slots) > 12 or any(s["task"] not in ("wp01", "wp02", "wp05") for s in slots):
            raise ValueError("exploration_ceiling")
        slots = [s for s in slots if batch == "all" or (s["arm"] == "A" if batch == "baseline" else s["arm"] == "B")]
    for slot in slots:
        if not re.fullmatch(SLOT_PATTERN, slot["slot_id"]):
            raise ValueError("invalid_slot_identifier")
    attempted = history(mode, manifest_id)
    return [s for s in slots if s["slot_id"] not in attempted], {
        s["slot_id"]: attempted[s["slot_id"]] for s in slots if s["slot_id"] in attempted}


def pairs(slots):
    """Keep both arms of a task/repetition in one ordered, short-lived job."""
    grouped = {}
    for slot in slots:
        grouped.setdefault((slot["task"], slot["repetition"]), []).append(slot["slot_id"])
    return [{"pair_id": "--".join(ids), "slots": ids} for ids in grouped.values()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("pilot", "final"))
    parser.add_argument("manifest_id")
    parser.add_argument("--batch", choices=("baseline", "treatment", "all"), default="all")
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args()
    if int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")) != 1 and not args.inspect:
        raise SystemExit("Same-run retries are disabled. Dispatch again to select genuinely unstarted slots.")
    if not args.inspect:
        from native_run import frozen_inputs
        frozen_inputs(args.manifest_id)
    slots, attempted = selection(args.mode, args.manifest_id, args.batch)
    if args.inspect:
        print(json.dumps({"truly_unstarted": slots, "previously_started": attempted}, indent=2))
    else:
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write("matrix=" + json.dumps({"include": pairs(slots)}, separators=(",", ":")) + "\n")
            output.write("has_slots=" + ("true" if slots else "false") + "\n")
        print("Selected", len(slots), "unstarted slots. Preserved", len(attempted), "prior attempts.")
