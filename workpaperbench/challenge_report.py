"""Regenerate challenge metrics from immutable scheduled attempt records."""
import hashlib
import json
from collections import Counter
from math import fsum
from pathlib import Path
from statistics import mean


def report_challenge(root):
    root = Path(root)
    output = root / "reports/challenge-v1"
    output.mkdir(parents=True, exist_ok=True)
    studies = []
    lines = ["# Research Challenge results", "", "Full dossiers, neutral shared instructions. Model comparisons are separate from the historical prompt-arm experiments.", ""]
    for path in sorted((root / "datasets/challenge-v1/manifests").glob("*.json")):
        manifest = json.loads(path.read_text())
        schedule = json.loads((root / manifest["schedule"]).read_text())
        schedule = schedule.get("slots", []) if isinstance(schedule, dict) else schedule
        rows = []
        for slot in schedule:
            directory = root / "reports/runs" / manifest["manifest_id"] / slot["slot_id"]
            record_path = directory / "record.json"
            record = json.loads(record_path.read_text()) if record_path.is_file() else None
            if record:
                if any(record.get(key) != slot[key] for key in ("task", "model_key", "condition", "repetition", "split")):
                    raise ValueError("challenge_record_schedule_mismatch")
                audit = json.loads((directory / "artifact-audit.json").read_text())
                if audit.get("archive_digest_verified") is not True or hashlib.sha256(record_path.read_bytes()).hexdigest() != audit["retained_file_sha256"]["record.json"]:
                    raise ValueError("challenge_record_provenance_unverified")
            rows.append({"slot": slot, "record": record})
        table = []
        for model_key in manifest["models"]:
            subsets = [("all", [r for r in rows if r["slot"]["model_key"] == model_key])]
            subsets += [(key, [r for r in rows if r["slot"]["model_key"] == model_key and r["slot"]["task"] == task["task_id"]]) for key, task in manifest["tasks"].items()]
            subsets += [("family-" + family, [r for r in rows if r["slot"]["model_key"] == model_key and r["slot"]["task"].removeprefix("challenge-v1-").startswith(family.lower())]) for family in "ABC"]
            for label, selected in subsets:
                verdicts = [r["record"]["verdict"] for r in selected if r["record"] and isinstance(r["record"].get("verdict"), dict)]
                metrics = {name: {"passed": sum(v.get("checks", {}).get(name) is True for v in verdicts),
                                  "assessed": sum(isinstance(v.get("checks", {}).get(name), bool) for v in verdicts)} for name in ("financial_answer", "evidence", "robustness", "delivery")}
                costs = [r["record"].get("provider_cost_delta_usd") if r["record"] else None for r in selected]
                known_costs = [v for v in costs if isinstance(v, (int, float)) and not isinstance(v, bool)]
                timing = [(r["record"].get("harbor_metrics") or {}).get("agent_execution_seconds") for r in selected if r["record"]]
                known_times = [v for v in timing if isinstance(v, (int, float)) and not isinstance(v, bool)]
                table.append({"scope": label, "model_key": model_key, "scheduled": len(selected), "verdict_coverage": len(verdicts),
                              "verified_research_completion": sum(v.get("verified_research_completion") is True for v in verdicts),
                              "strict_delivery_completion": sum(v.get("strict_delivery_completion") is True for v in verdicts), "components": metrics,
                              "known_slot_cost_usd": fsum(known_costs) if known_costs else None,
                              "unknown_cost_slots": len(selected) - len(known_costs),
                              "agent_execution_mean_seconds": mean(known_times) if known_times else None,
                              "unknown_latency_slots": len(selected) - len(known_times),
                              "failure_components_nonexclusive": {k: sum(v.get("checks", {}).get(k) is False for v in verdicts) for k in metrics},
                              "statuses": dict(Counter(r["record"].get("status") if r["record"] else "not_recorded" for r in selected))})
        actual = sorted((r for r in rows if r["record"] and r["record"].get("execution_started_at")), key=lambda r: r["record"]["execution_started_at"])
        studies.append({"manifest_id": manifest["manifest_id"], "stage": manifest["stage"], "models": manifest["models"], "metrics": table,
                        "actual_start_order": [r["slot"]["slot_id"] for r in actual],
                        "scheduled_order": [r["slot"]["slot_id"] for r in rows],
                        "task_macro_completion": {key: sum(r["verified_research_completion"] / r["scheduled"] for r in table if r["model_key"] == key and r["scope"] in manifest["tasks"]) / len(manifest["tasks"]) for key in manifest["models"]},
                        "slots": [{"slot_id": r["slot"]["slot_id"], "status": r["record"].get("status") if r["record"] else "not_recorded", "started_at": r["record"].get("execution_started_at") if r["record"] else None,
                                   "latency_seconds": (r["record"].get("harbor_metrics") or {}).get("agent_execution_seconds") if r["record"] else None,
                                   "provider_cost_delta_usd": r["record"].get("provider_cost_delta_usd") if r["record"] else None,
                                   "errors": (r["record"].get("verdict") or {}).get("errors", []) if r["record"] else []} for r in rows]})
        lines += ["## " + manifest["stage"] + " - " + manifest["manifest_id"], "", "| Scope | Model | Financial / assessed | Evidence / assessed | Robustness / assessed | Verified / scheduled | Delivery / assessed | Strict / scheduled | Verdict coverage |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for row in table:
            cell = lambda key: str(row["components"][key]["passed"]) + " / " + str(row["components"][key]["assessed"])
            lines.append("| " + " | ".join((row["scope"], row["model_key"], cell("financial_answer"), cell("evidence"), cell("robustness"), f"{row['verified_research_completion']} / {row['scheduled']}", cell("delivery"), f"{row['strict_delivery_completion']} / {row['scheduled']}", f"{row['verdict_coverage']} / {row['scheduled']}")) + " |")
        lines += ["", "Balanced repetitions give equal weight to each task in the scheduled completion proportions. Component denominators count assessed verdicts. Missing or infrastructure-failed slots remain in scheduled denominators and are not fabricated model answers.", ""]
        lines += ["Latency, actual order, per-model cost deltas, unknown counts and nonexclusive failed components are retained in scores.json. Provider metadata can lag, so slot cost deltas are not exact model allocations. Native zero token fields do not establish zero usage.", ""]
    lines += ["No assisted-condition trials are recorded. These small source groups and repeated attempts do not establish population reliability or a universal model ranking. Synthetic controls test a few declared mechanisms, not universal generalization.", ""]
    result = {"dataset_id": "challenge-v1", "studies": studies}
    (output / "scores.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "results.md").write_text("\n".join(lines))
    return result
