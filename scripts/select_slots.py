"""Use the committed schedule and Actions history to avoid repeating started slots."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path]))


def job_started(job):
    if job.get("status") == "queued" or job.get("conclusion") == "skipped":
        return False
    if job.get("runner_id") or any(step.get("started_at") for step in job.get("steps", [])):
        return True
    return job.get("status") == "in_progress" or (
        job.get("conclusion") == "failure" and bool(job.get("started_at")))


def selection(mode, manifest_id, batch):
    if mode == "final":
        manifest = json.loads((ROOT / "config/freeze.json").read_text())
        if manifest_id != manifest["manifest_id"]:
            raise ValueError("manifest mismatch")
        slots = json.loads((ROOT / "config/schedule.json").read_text())
    else:
        if manifest_id != "development-v1":
            raise ValueError("pilot manifest mismatch")
        slots = json.loads((ROOT / "config/pilot.json").read_text())
        if len(slots) > 12 or any(s["task"] not in ("wp01", "wp02", "wp05") for s in slots):
            raise ValueError("exploration ceiling")
        slots = [s for s in slots if batch == "all" or (s["arm"] == "A" if batch == "baseline" else s["arm"] == "B")]
    for slot in slots:
        if not re.fullmatch(r"(?:pilot|final)-wp0[1-8]-[AB]-[1-3]", slot["slot_id"]):
            raise ValueError("invalid slot identifier")
    attempted = {}
    for page in range(1, 11):
        response = api(f"repos/CaoimhConway/workpaperbench/actions/workflows/benchmark.yml/runs?per_page=100&page={page}")
        runs = response["workflow_runs"]
        for run in runs:
            if run["id"] == int(os.environ.get("GITHUB_RUN_ID", "0")):
                continue
            jobs = api(f"repos/CaoimhConway/workpaperbench/actions/runs/{run['id']}/jobs?filter=all&per_page=100")["jobs"]
            for job in jobs:
                name = job["name"]
                if name.startswith("trial-") and job_started(job):
                    attempted[name.removeprefix("trial-")] = {"run_id": run["id"], "conclusion": job["conclusion"], "status": job["status"]}
        if len(runs) < 100:
            break
    selected = [s for s in slots if s["slot_id"] not in attempted]
    return selected, {s["slot_id"]: attempted[s["slot_id"]] for s in slots if s["slot_id"] in attempted}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("pilot", "final"))
    parser.add_argument("manifest_id")
    parser.add_argument("--batch", choices=("baseline", "treatment", "all"), default="all")
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args()
    slots, attempted = selection(args.mode, args.manifest_id, args.batch)
    if args.inspect:
        print(json.dumps({"truly_unstarted": slots, "previously_started": attempted}, indent=2))
    else:
        result = json.dumps({"include": slots}, separators=(",", ":"))
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write("matrix=" + result + "\n")
            output.write("has_slots=" + ("true" if slots else "false") + "\n")
        print("Selected", len(slots), "unstarted slots. Preserved", len(attempted), "prior attempts.")
