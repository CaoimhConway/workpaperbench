"""Inspect workpapers and render results from persisted slot records."""
import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import mean

from .grading import parse, validate


ROOT = Path(__file__).resolve().parent.parent


def report(root):
    root = Path(root)
    manifest = json.loads((root / "config/freeze.json").read_text())
    schedule = json.loads((root / "config/schedule.json").read_text())
    records = {}
    supplemental = []
    for path in sorted((root / "reports/runs").glob("**/record.json")):
        record = json.loads(path.read_text())
        if record["campaign"] != "final":
            supplemental.append(record)
            continue
        if record["slot_id"] in records:
            raise ValueError("duplicate final slot record " + record["slot_id"])
        records[record["slot_id"]] = record
    by_id = {slot["slot_id"]: slot for slot in schedule}
    for identifier, record in records.items():
        if identifier not in by_id:
            raise ValueError("unscheduled final slot " + identifier)
        if any(record.get(key) != by_id[identifier][key] for key in ("task", "arm", "repetition", "split")):
            raise ValueError("slot identity mismatch " + identifier)
        if "hashes" in manifest and record.get("freeze_manifest_id") != manifest["manifest_id"]:
            raise ValueError("slot freeze mismatch " + identifier)
    rows = []
    for slot in schedule:
        row = {**slot, **records.get(slot["slot_id"], {"status": "unstarted", "verdict": None})}
        rows.append(row)
    summaries = {}
    for split in ("evaluation", "development"):
        summaries[split] = {}
        for arm in ("A", "B"):
            selected = [r for r in rows if r["split"] == split and r["arm"] == arm]
            passed = sum(bool(r.get("verdict") and r["verdict"].get("complete")) for r in selected)
            categories = Counter()
            checks = Counter()
            na = Counter()
            gap = 0
            for row in selected:
                verdict = row.get("verdict") or {}
                flags = verdict.get("checks") or {}
                for key, value in flags.items():
                    if value is True:
                        checks[key] += 1
                    elif value is None:
                        na[key] += 1
                if flags.get("numerical") is True and not verdict.get("complete"):
                    gap += 1
                    if any(flags.get(k) is False for k in ("evidence_context", "availability", "conclusion")):
                        categories["substantive"] += 1
                    if flags.get("replay") is False:
                        categories["replay"] += 1
                    if flags.get("format") is False or row["status"] not in ("complete", "task_failed"):
                        categories["format_or_infrastructure"] += 1
            summaries[split][arm] = {"scheduled": len(selected), "verified": passed,
                                      "numerical_correct_full_failed": gap,
                                      "gap_causes_nonexclusive": dict(categories), "checks_passed": dict(checks),
                                      "statuses": dict(Counter(r["status"] for r in selected)), "checks_na": dict(na)}
            for phase in ("agent_setup", "agent_execution", "verifier"):
                values = [(r.get("harbor_metrics") or {}).get(phase + "_seconds") for r in selected]
                known = [v for v in values if isinstance(v, (int, float))]
                summaries[split][arm][phase + "_mean_seconds"] = mean(known) if known else None
            costs = [r.get("provider_cost_delta_usd") for r in selected]
            known = [v for v in costs if isinstance(v, (int, float))]
            summaries[split][arm]["known_slot_cost_usd"] = sum(known) if known else None
            summaries[split][arm]["unknown_cost_slots"] = len(costs) - len(known)
    snapshots = [json.loads(path.read_text()) for path in (root / "reports/provider").glob("*.json")]
    latest = max(snapshots, key=lambda item: item["as_of"], default=None)
    lifetime = latest["snapshot"].get("usage_usd") if latest else None
    verified_all = sum(bool((r.get("verdict") or {}).get("complete")) for r in rows + supplemental)
    cost = {"latest_provider_snapshot": latest, "lifetime_inference_usd": lifetime,
            "all_verified_completions": verified_all,
            "lifetime_cost_per_verified_completion_usd": lifetime / verified_all if lifetime is not None and verified_all else None,
            "allocation_note": "Lifetime includes exploratory and failed calls. Slot deltas can lag and are not an exact allocation. Native zero token fields do not establish zero usage."}
    result = {"manifest": manifest, "summary": summaries, "slots": rows, "exploratory": supplemental, "cost": cost}
    output = root / "reports"
    output.mkdir(exist_ok=True)
    (output / "scores.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# Results", "", "Computed from saved sanitized records. Every scheduled slot remains visible.", "",
             "| Split | Arm | Verified / scheduled | Numbers correct, full task failed |", "|---|---|---:|---:|"]
    for split, arms in summaries.items():
        for arm, summary in arms.items():
            lines.append(f"| {split} | {arm} | {summary['verified']} / {summary['scheduled']} | {summary['numerical_correct_full_failed']} |")
    lines += ["", "Diagnostic flags count passes over the scheduled denominator. N/A flags are not passes.", "",
              "| Split | Arm | Format | Numerical | Evidence/context | Availability | Replay | Conclusion | Status counts |",
              "|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for split, arms in summaries.items():
        for arm, summary in arms.items():
            counts = summary["checks_passed"]
            diagnostics = " | ".join(f"{counts.get(key, 0)} / {summary['scheduled']} (N/A {summary['checks_na'].get(key, 0)})" for key in ("format", "numerical", "evidence_context", "availability", "replay", "conclusion"))
            lines.append(f"| {split} | {arm} | {diagnostics} | {summary['statuses']} |")
    lines += ["",
              "| Slot | Status | Verified | Run | Errors |", "|---|---|---|---|---|"]
    for row in rows:
        verdict = row.get("verdict") or {}
        errors = ", ".join(verdict.get("errors", []))
        lines.append(f"| {row['slot_id']} | {row['status']} | {verdict.get('complete', 'N/A')} | {row.get('run_id', 'N/A')} | {errors} |")
    lines += ["", "| Task | Arm | Verified / 3 | Origin | Source group |", "|---|---|---:|---|---|"]
    for task in sorted({r["task"] for r in rows}):
        for arm in ("A", "B"):
            selected = [r for r in rows if r["task"] == task and r["arm"] == arm]
            passed = sum(bool((r.get("verdict") or {}).get("complete")) for r in selected)
            sample = next((r for r in selected if r.get("source_group")), {})
            lines.append(f"| {task} | {arm} | {passed} / {len(selected)} | {sample.get('task_origin', 'unrecorded')} | {sample.get('source_group', 'unrecorded')} |")
    lines += ["", "Cost, latency and diagnostic flags (JSON detail includes all checks and unknowns):", ""]
    lines += ["| Split | Arm | Known slot cost USD | Unknown cost slots | Mean solve seconds | Gap causes |", "|---|---|---:|---:|---:|---|"]
    for split, arms in summaries.items():
        for arm, summary in arms.items():
            lines.append(f"| {split} | {arm} | {summary['known_slot_cost_usd']} | {summary['unknown_cost_slots']} | {summary['agent_execution_mean_seconds']} | {summary['gap_causes_nonexclusive']} |")
    finished = sum(r["status"] != "unstarted" for r in rows)
    lines += ["", f"Recorded final slots: {finished} / {len(rows)}. Exploratory records: {len(supplemental)}.",
              f"Provider lifetime inference USD: {lifetime}. As of: {latest['as_of'] if latest else 'unknown'}.",
              f"All verified completions, including exploration: {verified_all}. Lifetime cost per verified completion USD: {cost['lifetime_cost_per_verified_completion_usd']}.",
              cost["allocation_note"],
              "No verified completions means cost per completion is undefined, not zero. Missing usage is unknown.",
              "Related source groups and repeated attempts are not independent datasets."]
    (output / "results.md").write_text("\n".join(lines) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("validate")
    inspect.add_argument("path", type=Path)
    sub.add_parser("demo")
    sub.add_parser("report")
    args = parser.parse_args()
    if args.command == "validate":
        answer = parse(args.path.read_bytes())
        validate(answer, json.loads((ROOT / "config/schema.json").read_text()))
        print("Output structure valid. Financial correctness and replay require the separate verifier on Actions.")
    elif args.command == "demo":
        reference = json.loads((ROOT / "tasks/wp01/tests/reference.json").read_text())
        print("Authored source-backed workpaper, not a live submission")
        print(json.dumps(reference, indent=2))
    else:
        result = report(ROOT)
        print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
