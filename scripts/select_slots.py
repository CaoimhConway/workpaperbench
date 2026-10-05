"""Select experiment-scoped slots without repeating an attempted execution."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
REPO = "CaoimhConway/workpaperbench"
SLOT_PATTERN = r"(?:pilot-wp0[1-8]-[AB]-[1-9]|final-wp0[1-8]-[AB]-[1-3])"


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path]))


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
        jobs = list(pages(f"repos/{REPO}/actions/runs/{run['id']}/jobs?filter=all", "jobs"))
        jobs = [job for job in jobs if any(s.startswith(mode + "-") for s in job_slots(job))]
        if not jobs or run_manifest(run, mode, cache) != manifest_id:
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
    if mode == "final":
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
    if args.mode == "final" and not args.inspect:
        from native_run import frozen_inputs
        frozen_inputs()
    slots, attempted = selection(args.mode, args.manifest_id, args.batch)
    if args.inspect:
        print(json.dumps({"truly_unstarted": slots, "previously_started": attempted}, indent=2))
    else:
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write("matrix=" + json.dumps({"include": pairs(slots)}, separators=(",", ":")) + "\n")
            output.write("has_slots=" + ("true" if slots else "false") + "\n")
        print("Selected", len(slots), "unstarted slots. Preserved", len(attempted), "prior attempts.")
