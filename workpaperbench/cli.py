"""Inspect workpapers and report original and reviewed verdicts separately."""
import argparse
from collections import Counter
import json
from math import fsum
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
            checks, unknown, assessed_checks, causes = Counter(), Counter(), Counter(), Counter()
            gap = 0
            for row in selected:
                verdict = row.get("verdict") or {}
                flags = verdict.get("checks") or {}
                detail = (verdict.get('details') or {}).get('conclusion') or {}
                flags = {**flags, **{'conclusion_' + k: detail.get(k) for k in ('verdict', 'reason_code', 'evidence')}}
                for key in ("format", "numerical", "evidence_context", "availability", "replay", "conclusion",
                            "conclusion_verdict", "conclusion_reason_code", "conclusion_evidence"):
                    if isinstance(flags.get(key), bool):
                        assessed_checks[key] += 1
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
                        causes['conclusion_reason_or_evidence' if detail else 'conclusion_contract_unsplit'] += 1
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
                "checks_assessed": dict(assessed_checks),
                "checks_na": dict(unknown), "statuses": dict(Counter(r["status"] for r in selected)),
                "known_slot_cost_usd": fsum(known_cost) if known_cost else None,
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
        if str(record.get("experiment_id", "")).startswith(("real-v1", "challenge-v1")):
            continue
        if record["campaign"] != "final" or (record.get('freeze_manifest_id') is not None
                and record['freeze_manifest_id'] != manifest['manifest_id']):
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
    scorer_identities = {(v.get("scorer_version"), v.get("scorer_sha256")) for v in reviews.values()}
    if len(scorer_identities) > 1:
        raise ValueError("mixed reviewed scorer versions")
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
    expected_order = [s['slot_id'] for s in schedule]
    changes = [{'slot_id': r['slot_id'], 'original_complete': r['verdict']['complete'],
                'reviewed_complete': reviews[r['slot_id']]['verdict']['complete'],
                'original_errors': r['verdict'].get('errors', []),
                'reviewed_errors': reviews[r['slot_id']]['verdict'].get('errors', []),
                'input_file': reviews[r['slot_id']]['input_file'],
                'input_sha256': reviews[r['slot_id']]['input_sha256']}
               for r in rows if r.get('verdict') and r['slot_id'] in reviews
               and r['verdict']['complete'] != reviews[r['slot_id']]['verdict']['complete']]
    result = {"manifest": manifest, "summary": summaries, "reviewed_summary": reviewed_summary,
              "slots": rows, "reviews": reviews, "exploratory": supplemental, "cost": cost,
              "reconciliation": reconciliation, "actual_start_order": actual_order,
              "order_matches_schedule": actual_order == expected_order,
              "score_changes": changes,
              "reviewed_scorer": list(next(iter(scorer_identities))) if scorer_identities else None}
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
    lines += ['', '## Numerical and independent checks', '',
              'Passes / assessed checks are shown beside the planned counts above. Null checks are unassessed or inapplicable. Legacy conclusions cannot be split retrospectively without regrading.', '',
              '| Scorer | Split | Arm | Numbers | Format | Evidence | Units/availability | SQL replay | Conclusion verdict | Conclusion reason | Conclusion evidence |',
              '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for label, table in (('Original', summaries), ('Corrected', reviewed_summary)):
        for split, arms in table.items():
            for arm, summary in arms.items():
                cells = []
                for key in ('numerical', 'format', 'evidence_context', 'availability', 'replay',
                            'conclusion_verdict', 'conclusion_reason_code', 'conclusion_evidence'):
                    n = summary['checks_assessed'].get(key, 0)
                    cells.append(f"{summary['checks_passed'].get(key, 0)} / {n}" if n else 'Unassessed')
                lines.append('| ' + ' | '.join([label, split, arm, *cells]) + ' |')
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
    lines += ['', '## Task outcomes and origins', '',
              '| Task | Arm | Original complete / planned | Corrected complete / planned | Corrected coverage | Origin | Source group |',
              '|---|---|---:|---:|---:|---|---|']
    for task in sorted({r['task'] for r in rows}):
        for arm in ('A', 'B'):
            selected = [r for r in rows if r['task'] == task and r['arm'] == arm]
            if not selected:
                continue
            original = sum(bool((r.get('verdict') or {}).get('complete')) for r in selected)
            corrected = sum(bool(reviews.get(r['slot_id'], {}).get('verdict', {}).get('complete')) for r in selected)
            coverage = sum(r['slot_id'] in reviews for r in selected)
            source = selected[0]
            original_cell = f"{original} / {len(selected)}" if any(r.get('verdict') is not None for r in selected) else 'Not assessed'
            corrected_cell = f"{corrected} / {len(selected)}" if coverage else 'Not assessed'
            lines.append(f"| {task} | {arm} | {original_cell} | {corrected_cell} | {coverage} / {len(selected)} | {source.get('task_origin', 'Unknown')} | {source.get('source_group', 'Unknown')} |")
    lines += ['', '## Score changes and retained input', '',
              f"Corrected scorer identity: `{result['reviewed_scorer']}`. Full input hashes, original diagnostics and corrected diagnostics are in [scores.json](scores.json).", '',
              f"Strict completion changes among regraded slots: **{len(changes)}**."]
    for change in changes:
        lines.append(f"- {change['slot_id']}: {change['original_complete']} to {change['reviewed_complete']}. Original errors {change['original_errors']}. Corrected errors {change['reviewed_errors']}.")
    unavailable = [r['slot_id'] for r in rows if r['slot_id'] not in reviews]
    lines += ['', 'Not regraded: ' + (', '.join(unavailable) if unavailable else 'None') + '.',
              'Historical normalized JSON is the input where original bytes are missing. It is never relabeled as original serialization. Missing answer bytes cannot yield a corrected verdict. Previous regrades remain under their content hashes.']
    lines += ["", "## Cost and interpretation", "", f"Provider snapshot lifetime use: **{lifetime if lifetime is not None else 'Unknown'} USD**.",
              f"Snapshot time: {latest['as_of'] if latest else 'Unknown'}. Original verified completions recorded by that snapshot: {verified_all}.",
              cost['allocation_note'], "", "A and B use the same model. This is a small regression study, not a model leaderboard, significance test or production-reliability estimate.",
              "The original matrix limited concurrency but did not enforce pair order. Actual start order and per-slot latency/cost/diagnostic fields are preserved in scores.json.",
              "Five evaluation tasks are not five independent datasets. Two share the synthetic acquisition fallback. Development and evaluation remain separate."]
    lines += ['', '| Split | Arm | Mean solve seconds | Recorded snapshot deltas USD | Unknown delta slots |',
              '|---|---|---:|---:|---:|']
    for split, arms in summaries.items():
        for arm, summary in arms.items():
            timing = summary['agent_execution_mean_seconds']
            delta = summary['known_slot_cost_usd']
            lines.append(f"| {split} | {arm} | {timing:.2f} | {delta:.6f} | {summary['unknown_cost_slots']} |" if timing is not None and delta is not None
                         else f"| {split} | {arm} | Unknown | Unknown | {summary['unknown_cost_slots']} |")
    lines += ['', f"Actual start order matches the preserved schedule: **{result['order_matches_schedule']}**. Recorded order: " + ', '.join(actual_order) + '.',
              '', f"Supplementary records: **{len(supplemental)}**. Their statuses, costs and original verdicts remain in scores.json. No additional inference was used for correction."]
    (output / "results.md").write_text("\n".join(lines) + "\n")
    update_readme(root, result)
    return result



def update_readme(root, result):
    """Refresh only the marked results block from persisted evidence."""
    path = Path(root) / "README.md"
    if not path.is_file():
        return
    text = path.read_text()
    begin, end = "<!-- study-results:start -->", "<!-- study-results:end -->"
    if begin not in text and end not in text:
        return
    if text.count(begin) != 1 or text.count(end) != 1 or text.index(begin) >= text.index(end):
        raise ValueError("invalid README result markers")
    rows = result["slots"]
    assessed = sum(r.get("verdict") is not None for r in rows)
    reviewed = len(result["reviews"])
    terminal = sum(r["status"] in TERMINAL | {"infra_failed", "blocked", "artifact_missing"} for r in rows)
    state = "All scheduled attempts accounted for" if terminal == len(rows) else "Partial campaign"
    lines = [begin, "", f"**{state}.** Original verdicts: **{assessed}/{len(rows)}**. Corrected verdicts: **{reviewed}/{len(rows)}**.", "",
             "| Evaluation arm | Original complete / planned | Corrected complete / planned | Corrected numerical / assessed | Corrected coverage |",
             "|---|---:|---:|---:|---:|"]
    for arm in ("A", "B"):
        original = result["summary"]["evaluation"][arm]
        correction = result["reviewed_summary"]["evaluation"][arm]
        def cell(summary):
            return f"{summary['verified']} / {summary['scheduled']}" if summary["assessed"] else "Not assessed"
        numerical = correction.get('checks_assessed', {}).get('numerical', 0)
        numbers = f"{correction.get('checks_passed', {}).get('numerical', 0)} / {numerical}" if numerical else 'Unassessed'
        lines.append(f"| {arm} | {cell(original)} | {cell(correction)} | {numbers} | {correction['assessed']} / {correction['scheduled']} |")
    lines += ["", "Only evaluation tasks appear here. Development is reported separately. Unfinished or unreviewable trials are not observed zero-score answers. These are coverage-aware counts, not a treatment-effect claim.", "",
              "[Full results, failures, costs and original records](reports/results.md)", "", end]
    prefix, remainder = text.split(begin, 1)
    _, suffix = remainder.split(end, 1)
    path.write_text(prefix + "\n".join(lines) + suffix)

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("validate")
    inspect.add_argument("path", type=Path)
    sub.add_parser("demo")
    reporting = sub.add_parser("report")
    reporting.add_argument("--dataset", choices=("all", "historical", "real-v1", "challenge-v1"), default="all")
    args = parser.parse_args()
    if args.command == "validate":
        answer = parse(args.path.read_bytes())
        task_id = str(answer.get("task_id", ""))
        schema_path = ROOT / ("datasets/challenge-v1/schema.json" if task_id.startswith("challenge-v1-") else "datasets/real-v1/schema.json" if task_id.startswith("real-v1-") else "config/schema.json")
        challenge_ids = {f"challenge-v1-{family}{number:02}" for family in "abc" for number in range(1, 5)}
        if task_id in challenge_ids:
            schema_path = ROOT / "datasets/challenge-v1/tasks" / task_id.removeprefix("challenge-v1-") / "environment/schema.json"
        validate(answer, json.loads(schema_path.read_text()))
        print("Output structure valid. Financial correctness and replay require the separate verifier on Actions.")
    elif args.command == "demo":
        challenge = ROOT / 'datasets/challenge-v1/tasks/a01/tests/reference.json'
        if challenge.is_file():
            workpaper = json.loads(challenge.read_text())
            print('Authored Research Challenge reference: Adobe Q4 FY2024 guidance and reconciliation')
            for claim in workpaper['answers']:
                print(f"{claim['id']}: {claim['value']} {claim['unit']}. Evidence: {claim['evidence']}")
            print('Evidence: datasets/challenge-v1/tasks/a01/environment/sources.md. No submitted SQL executes in this demo.')
            print()
        reference_path = ROOT / 'datasets/real-v1/tasks/wp04/tests/reference.json'
        if reference_path.is_file():
            workpaper = json.loads(reference_path.read_text())
            label = 'Authored reference'
            manifest_path = ROOT / 'datasets/real-v1/manifest.json'
            if manifest_path.is_file():
                manifest = json.loads(manifest_path.read_text())
                for directory in sorted((ROOT / 'reports/runs' / manifest['manifest_id']).glob('final-wp04-*')):
                    if (directory / 'answer.json').is_file() and (directory / 'verdict.json').is_file():
                        verdict = json.loads((directory / 'verdict.json').read_text())
                        if verdict.get('complete') is True:
                            workpaper = json.loads((directory / 'answer.json').read_text())
                            label = 'Recorded source-backed submission ' + directory.name
                            break
            print(label + ': Circle January 2025 reserve workpaper')
            for claim in workpaper['answers']:
                print(f"{claim['id']}: {claim['value']} {claim['unit']}. Evidence: {claim['evidence']}")
            print('See README for source dates, definitions and SQL. This display executes no submitted SQL.')
            print()
        print('Historical synthetic formula case:')
        saved = json.loads((ROOT / 'reports/runs/final-wp03-A-1/answer.json').read_text())
        record = json.loads((ROOT / 'reports/runs/final-wp03-A-1/record.json').read_text())
        claims = {c['id']: c for c in saved['answers']}
        print("A correct answer can conceal an incorrect formula.")
        print(f"Recorded wp03 A1: P1={claims['p1_total']['value']:g}, P2={claims['p2_total']['value']:g}, reported growth={claims['as_of_growth']['value']:g}%.")
        print(f"Original complete={record['verdict']['complete']}. Original checks={record['verdict']['checks']}.")
        print("Submitted expression: P2 - P1 * 100.0 / P1.")
        print("Changed fixture: P1=120, P2=150. Expression=50%, correct growth=25%.")
        print("This display does not execute submitted SQL. See reports/case-study.md for the unchanged artifact and qualifications.")
    else:
        if args.dataset == 'historical' or (args.dataset == 'all' and not (ROOT / 'datasets/real-v1/manifest.json').is_file()):
            result = report(ROOT)
            print(json.dumps(result['summary'], indent=2))
        if args.dataset in ('all', 'real-v1'):
            from .real_report import report_real
            result = report_real(ROOT)
            if result is not None:
                print(json.dumps(result['summary'], indent=2))
        if args.dataset in ('all', 'challenge-v1') and (ROOT / 'datasets/challenge-v1').is_dir():
            from .challenge_report import report_challenge
            result = report_challenge(ROOT)
            print('Research Challenge report regenerated for', len(result['studies']), 'frozen stages')


if __name__ == "__main__":
    main()
