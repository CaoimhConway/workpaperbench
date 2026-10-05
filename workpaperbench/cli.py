"""Inspect workpapers and report original and reviewed verdicts separately."""
import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import mean

from .grading import parse, validate

ROOT = Path(__file__).resolve().parent.parent
TERMINAL = {"complete", "task_failed"}


def summarize(rows):
    summaries = {}
    for split in ("evaluation", "development"):
        summaries[split] = {}
        for arm in ("A", "B"):
            selected = [r for r in rows if r["split"] == split and r["arm"] == arm]
            checks, unknown, causes = Counter(), Counter(), Counter()
            gap = 0
            for row in selected:
                verdict = row.get("verdict") or {}
                flags = verdict.get("checks") or {}
                for key in ("format", "numerical", "evidence_context", "availability", "replay", "conclusion"):
                    if flags.get(key) is True:
                        checks[key] += 1
                    elif flags.get(key) is None:
                        unknown[key] += 1
                if flags.get("numerical") is True and not verdict.get("complete"):
                    gap += 1
                    if flags.get("evidence_context") is False:
                        causes["evidence_requirements"] += 1
                    if flags.get("availability") is False:
                        causes["availability_or_unit"] += 1
                    conclusion = (verdict.get("details") or {}).get("conclusion")
                    if conclusion and conclusion.get("verdict") is False:
                        causes["wrong_conclusion_verdict"] += 1
                    elif flags.get("conclusion") is False:
                        causes["conclusion_contract_unsplit"] += 1
                    if flags.get("replay") is False:
                        causes["replay"] += 1
                    if flags.get("format") is False:
                        causes["format"] += 1
            passed = sum(r["status"] in TERMINAL and bool((r.get("verdict") or {}).get("complete")) for r in selected)
            costs = [r.get("provider_cost_delta_usd") for r in selected]
            known_cost = [v for v in costs if isinstance(v, (int, float)) and not isinstance(v, bool)]
            timing = [(r.get("harbor_metrics") or {}).get("agent_execution_seconds") for r in selected]
            known_time = [v for v in timing if isinstance(v, (int, float))]
            summaries[split][arm] = {
                "scheduled": len(selected), "verified": passed,
                "assessed": sum(r.get("verdict") is not None for r in selected),
                "numerical_correct_full_failed": gap,
                "gap_causes_nonexclusive": dict(causes), "checks_passed": dict(checks),
                "checks_na": dict(unknown), "statuses": dict(Counter(r["status"] for r in selected)),
                "known_slot_cost_usd": sum(known_cost) if known_cost else None,
                "unknown_cost_slots": len(costs) - len(known_cost),
                "agent_execution_mean_seconds": mean(known_time) if known_time else None,
            }
    return summaries


def report(root):
    root = Path(root)
    manifest = json.loads((root / "config/freeze.json").read_text())
    schedule = json.loads((root / "config/schedule.json").read_text())
    records, reviews, supplemental = {}, {}, []
    for path in sorted((root / "reports/runs").glob("**/record.json")):
        record = json.loads(path.read_text())
        if record["campaign"] != "final":
            supplemental.append(record)
            continue
        if record["slot_id"] in records:
            raise ValueError("duplicate final slot record " + record["slot_id"])
        records[record["slot_id"]] = record
        review_path = path.with_name("regrade.json")
        if review_path.is_file():
            review = json.loads(review_path.read_text())
            if review.get("manifest_id") != manifest["manifest_id"]:
                raise ValueError("regrade manifest mismatch")
            from .grading import digest
            original_name = review.get("input_file")
            if original_name not in ("answer.json", "answer.raw.txt") or digest(path.with_name(original_name)) != review.get("input_sha256"):
                raise ValueError("regrade input mismatch")
            reviews[record["slot_id"]] = review
    by_id = {slot["slot_id"]: slot for slot in schedule}
    if len(by_id) != len(schedule):
        raise ValueError("duplicate scheduled slot")
    for identifier, record in records.items():
        if identifier not in by_id:
            raise ValueError("unscheduled final slot " + identifier)
        if any(record.get(key) != by_id[identifier][key] for key in ("task", "arm", "repetition", "split")):
            raise ValueError("slot identity mismatch " + identifier)
        if "hashes" in manifest and record.get("freeze_manifest_id") != manifest["manifest_id"]:
            raise ValueError("slot freeze mismatch " + identifier)
    reconciliation_path = root / "reports/reconciliation.json"
    reconciliation = json.loads(reconciliation_path.read_text()) if reconciliation_path.is_file() else {}
    if reconciliation and reconciliation.get("manifest_id") != manifest["manifest_id"]:
        raise ValueError("reconciliation manifest mismatch")
    rows = []
    for slot in schedule:
        absent = {"status": "unrecorded", "verdict": None, **reconciliation.get("slots", {}).get(slot["slot_id"], {})}
        row = {**slot, **records.get(slot["slot_id"], absent)}
        source_path = root / "sources" / (slot["task"] + ".json")
        if source_path.is_file():
            source = json.loads(source_path.read_text())
            row.setdefault("task_origin", source.get("origin"))
            row.setdefault("source_group", source.get("source_group"))
        rows.append(row)
    summaries = summarize(rows)
    reviewed_rows = [{**row, "verdict": reviews.get(row["slot_id"], {}).get("verdict")} for row in rows]
    reviewed_summary = summarize(reviewed_rows)
    snapshots = [json.loads(path.read_text()) for path in (root / "reports/provider").glob("*.json")]
    for record in records.values():
        if record.get("provider_after") and record.get("finished_at"):
            snapshots.append({"as_of": record["finished_at"], "run_id": record.get("run_id"),
                              "snapshot": record["provider_after"], "source": "lagging_slot_snapshot"})
    latest = max(snapshots, key=lambda item: item["as_of"] , default=None)
    lifetime = latest["snapshot"].get("usage_usd") if latest else None
    # Align this diagnostic denominator with the snapshot, never future completions.
    eligible = [r for r in rows + supplemental if latest and r.get("finished_at") and r["finished_at"] <= latest["as_of"]]
    verified_all = sum(r["status"] in TERMINAL and bool((r.get("verdict") or {}).get("complete")) for r in eligible)
    cost = {"latest_provider_snapshot": latest, "lifetime_inference_usd": lifetime,
            "all_verified_completions": verified_all,
            "lifetime_cost_per_verified_completion_usd": lifetime / verified_all if lifetime is not None and verified_all else None,
            "allocation_note": "Lifetime includes exploration and failures. Snapshot reporting can lag. Slot deltas are not exact per-arm costs. Native zero token fields do not establish zero usage."}
    actual_order = [r["slot_id"] for r in sorted((r for r in rows if r.get("execution_started_at") or r.get("started_at")),
                    key=lambda r: r.get("execution_started_at") or r["started_at"])]
    result = {"manifest": manifest, "summary": summaries, "reviewed_summary": reviewed_summary,
              "slots": rows, "reviews": reviews, "exploratory": supplemental, "cost": cost,
              "reconciliation": reconciliation, "actual_start_order": actual_order}
    output = root / "reports"
    output.mkdir(exist_ok=True)
    (output / "scores.json").write_text(json.dumps(result, indent=2) + "\n")
    received = len(records)
    assessed = sum(r.get("verdict") is not None for r in rows)
    complete = received == len(schedule) and all(r["status"] in TERMINAL | {"infra_failed", "blocked", "artifact_missing"} for r in rows)
    lines = ["# Results", "", "**" + ("All scheduled attempts accounted for." if complete else "Partial campaign - not a finished comparison.") + "**", "",
             f"Imported final records: **{received}/{len(schedule)}**. Original verdicts available: **{assessed}**. Reviewed verdicts: **{len(reviews)}**.",
             "Unrecorded, queued and running slots are not zero-score model answers. Counts below retain the full planned denominator.",
             "Original verdicts are immutable. Reviewed verdicts are separate scorer-versioned checks of the same retained bytes, not new model trials.", "",
             "| Split | Arm | Original verified / planned | Original verdicts | Reviewed verified / planned | Reviewed verdicts |", "|---|---|---:|---:|---:|---:|"]
    for split, arms in summaries.items():
        for arm, summary in arms.items():
            reviewed = reviewed_summary[split][arm]
            def score(s):
                return str(s['verified']) + ' / ' + str(s['scheduled']) if s['assessed'] else 'Not available'
            lines.append(f"| {split} | {arm} | {score(summary)} | {summary['assessed']} | {score(reviewed)} | {reviewed['assessed']} |")
    lines += ["", "## Diagnose the failure, not just the score", "",
              "`None` means not assessed or not applicable, never a failed calculation. Evidence-ID requirements are distinct from semantic truth. Legacy conclusion checks combine verdict, reason and citations.", "",
              "| Scorer | Split | Arm | Numbers correct, full task failed | Observed causes (nonexclusive) |", "|---|---|---|---:|---|"]
    for label, table in (("Original", summaries), ("Reviewed", reviewed_summary)):
        for split, arms in table.items():
            for arm, s in arms.items():
                lines.append(f"| {label} | {split} | {arm} | {s['numerical_correct_full_failed']} | {s['gap_causes_nonexclusive']} |")
    lines += ["", "## Every scheduled slot", "", "| Slot | State | Original complete | Reviewed complete | Run | Original errors |", "|---|---|---|---|---|---|"]
    for row in rows:
        v = row.get("verdict") or {}
        rv = reviews.get(row["slot_id"], {}).get("verdict") or {}
        errors = ", ".join(v.get("errors", [])).replace("|", "\\|")
        lines.append(f"| {row['slot_id']} | {row['status']} | {v.get('complete', 'Not assessed')} | {rv.get('complete', 'Not assessed')} | {row.get('run_id', 'Unknown')} | {errors} |")
    lines += ["", "## Cost and interpretation", "", f"Provider snapshot lifetime use: **{lifetime if lifetime is not None else 'Unknown'} USD**.",
              f"Snapshot time: {latest['as_of'] if latest else 'Unknown'}. Original verified completions recorded by that snapshot: {verified_all}.",
              cost['allocation_note'], "", "A and B use the same model. This is a small regression study, not a model leaderboard, significance test or production-reliability estimate.",
              "The original matrix limited concurrency but did not enforce pair order. Actual start order and per-slot latency/cost/diagnostic fields are preserved in scores.json.",
              "Five evaluation tasks are not five independent datasets. Two share the synthetic acquisition fallback. Development and evaluation remain separate."]
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
        print("A correct answer can conceal an incorrect formula.")
        print("Recorded wp03 A1: P1=100, P2=120, reported growth=20%.")
        print("Submitted expression: P2 - P1 * 100.0 / P1.")
        print("Changed fixture: P1=120, P2=150. Expression=50%, correct growth=25%.")
        print("This display does not execute submitted SQL. See reports/case-study.md for the unchanged artifact and qualifications.")
    else:
        result = report(ROOT)
        print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
