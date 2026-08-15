"""Inspect workpapers and render results from persisted slot records."""
import argparse
from collections import Counter
import json
from pathlib import Path

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
            gap = 0
            for row in selected:
                verdict = row.get("verdict") or {}
                flags = verdict.get("checks") or {}
                for key, value in flags.items():
                    if value is True:
                        checks[key] += 1
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
                                      "gap_causes_nonexclusive": dict(categories), "checks_passed": dict(checks)}
    result = {"manifest": manifest, "summary": summaries, "slots": rows, "exploratory": supplemental}
    output = root / "reports"
    output.mkdir(exist_ok=True)
    (output / "scores.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# Results", "", "Generated from saved sanitized records. Every scheduled slot remains visible.", "",
             "| Split | Arm | Verified / scheduled | Numbers correct, full task failed |", "|---|---|---:|---:|"]
    for split, arms in summaries.items():
        for arm, summary in arms.items():
            lines.append(f"| {split} | {arm} | {summary['verified']} / {summary['scheduled']} | {summary['numerical_correct_full_failed']} |")
    lines += ["", "Diagnostic flags count passes over the scheduled denominator. N/A flags are not passes.", "",
              "| Slot | Status | Verified | Run | Errors |", "|---|---|---|---|---|"]
    for row in rows:
        verdict = row.get("verdict") or {}
        errors = ", ".join(verdict.get("errors", []))
        lines.append(f"| {row['slot_id']} | {row['status']} | {verdict.get('complete', 'N/A')} | {row.get('run_id', 'N/A')} | {errors} |")
    finished = sum(r["status"] != "unstarted" for r in rows)
    lines += ["", f"Recorded final slots: {finished} / {len(rows)}. Exploratory records: {len(supplemental)}.",
              "Cost totals use provider lifetime snapshots where available. Missing usage is unknown.",
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
