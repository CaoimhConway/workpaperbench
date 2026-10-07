"""Regenerate challenge metrics from immutable scheduled attempt records."""
import hashlib
import json
from collections import Counter
from math import fsum
from pathlib import Path
from statistics import mean


def failure_categories(record):
    if not record or not isinstance(record.get("verdict"), dict):
        return ["infrastructure_or_missing_outcome"]
    categories = set()
    for error in record["verdict"].get("errors", []):
        if error.startswith("delivery:"):
            categories.add("delivery")
        elif error.endswith(":unit"):
            categories.add("unit_representation_or_semantics")
        elif error.endswith(":evidence"):
            categories.add("evidence_support_or_contract")
        elif ":control:" in error or error.endswith(":original_replay"):
            categories.add("calculation_recomputation")
        elif error.endswith(":verdict") or error == "conclusion:missing":
            categories.add("bounded_conclusion")
        elif error.endswith((":numerical", ":availability")):
            categories.add("financial_value_or_availability")
    return sorted(categories)


def render_workpaper(answer, label, evidence_path):
    lines = ["# " + label, "", "Task: `" + answer["task_id"] + "`. [Frozen source dossier](" + evidence_path + ").", "",
             "| Claim | Availability | Value | Unit | Supporting sections |", "|---|---|---:|---|---|"]
    for claim in answer["answers"]:
        lines.append("| " + " | ".join((claim["id"], claim["status"], str(claim["value"]), claim["unit"], ", ".join(claim["evidence"]))) + " |")
    lines += ["", "Shared context: " + (", ".join(answer.get("context_evidence", [])) or "none"), ""]
    if answer["conclusion"]:
        lines += ["Original-dossier proposition verdict: **" + answer["conclusion"]["verdict"] + "**. Supporting sections: " + ", ".join(answer["conclusion"]["evidence"]) + ".", ""]
    for claim in answer["answers"]:
        if claim["sql"]:
            lines += ["## " + claim["id"], "", "```sql", claim["sql"], "```", ""]
    return "\n".join(lines)


def select_showcase(rows):
    """Apply the declared relevance rule in schedule order, without model preference."""
    delivered = [r for r in rows if r["record"]
                 and (r["record"].get("verdict") or {}).get("checks", {}).get("delivery") is True]
    substantive = [r for r in delivered if any(
        r["record"]["verdict"]["checks"].get(key) is False
        for key in ("financial_answer", "robustness"))]
    evidence = [r for r in delivered
                if r["record"]["verdict"]["checks"].get("evidence") is False]
    completed = [r for r in delivered
                 if r["record"]["verdict"].get("verified_research_completion") is True]
    candidates = substantive or evidence or completed
    primary = candidates[0] if candidates else None
    contrast = None
    if primary:
        successes = [r for r in completed if r is not primary]
        same_case = [r for r in successes if r["slot"]["task"] == primary["slot"]["task"]]
        contrast = next(iter(same_case or successes), None)
    return {"primary": primary, "contrast": contrast,
            "selection_kind": "financial_or_robustness_failure" if substantive else
                              "evidence_failure" if evidence else
                              "verified_completion" if completed else "no_delivered_outcome"}


def write_showcase(root, output, manifest, rows):
    selected = select_showcase(rows)
    result = {"rule": manifest.get("metrics", {}).get("showcase_selection"),
              "selection_kind": selected["selection_kind"],
              "interpretation": "Automatic diagnostic selection, not an independent capability-failure diagnosis"}
    for role in ("primary", "contrast"):
        row = selected[role]
        if row is None:
            result[role] = None
            continue
        slot = row["slot"]
        directory = root / "reports/runs" / manifest["manifest_id"] / slot["slot_id"]
        answer_path = directory / "answer.json"
        audit = json.loads((directory / "artifact-audit.json").read_text())
        if (not answer_path.is_file()
                or hashlib.sha256(answer_path.read_bytes()).hexdigest()
                != audit["retained_file_sha256"].get("answer.json")
                or audit["retained_file_sha256"].get("answer.json")
                != row["record"].get("retained_sha256")):
            raise ValueError("challenge_showcase_answer_provenance_unverified")
        answer = json.loads(answer_path.read_text())
        key = slot["task"].removeprefix("challenge-v1-")
        target = output / "workpapers" / manifest["manifest_id"] / (slot["slot_id"] + ".md")
        target.parent.mkdir(parents=True, exist_ok=True)
        dossier = "../../../../datasets/challenge-v1/tasks/" + key + "/environment/sources.md"
        target.write_text(render_workpaper(answer, "Saved " + slot["slot_id"] + " workpaper", dossier))
        result[role] = {"slot_id": slot["slot_id"], "task": slot["task"],
                        "model_key": slot["model_key"],
                        "workpaper": target.relative_to(root).as_posix(),
                        "answer_sha256": audit["retained_file_sha256"]["answer.json"],
                        "checks": row["record"]["verdict"]["checks"],
                        "errors": row["record"]["verdict"].get("errors", [])}
    return result


def report_challenge(root):
    root = Path(root)
    output = root / "reports/challenge-v1"
    output.mkdir(parents=True, exist_ok=True)
    reference = root / "datasets/challenge-v1/tasks/a01/tests/reference.json"
    if reference.is_file():
        (output / "reference-workpaper.md").write_text(render_workpaper(json.loads(reference.read_text()), "Authored Adobe reference workpaper", "../../datasets/challenge-v1/tasks/a01/environment/sources.md"))
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
        observers = [r["record"].get("native_api_retry_observer", {}) for r in rows if r["record"]]
        observed_retries = [o["observed_additional_attempts"] for o in observers
                            if o.get("capture_status") == "captured" and o.get("observer_registered") is True]
        showcase = write_showcase(root, output, manifest, rows) if manifest.get("metrics", {}).get("showcase_selection") else None
        studies.append({"manifest_id": manifest["manifest_id"], "stage": manifest["stage"], "models": manifest["models"], "metrics": table,
                        "showcase": showcase,
                        "scorer_version": manifest.get("scorer_version"),
                        "retry_observation": {"retained_records": len(observers),
                                              "capture_statuses": dict(Counter(o.get("capture_status", "not_recorded") for o in observers)),
                                              "captured_registered_slots": len(observed_retries),
                                              "observed_additional_attempts": sum(observed_retries) if observed_retries else None,
                                              "capture_completeness": "not_guaranteed",
                                              "provider_internal_retries": "unobserved"},
                        "actual_start_order": [r["slot"]["slot_id"] for r in actual],
                        "scheduled_order": [r["slot"]["slot_id"] for r in rows],
                        "task_macro_completion": {key: sum(r["verified_research_completion"] / r["scheduled"] for r in table if r["model_key"] == key and r["scope"] in manifest["tasks"]) / len(manifest["tasks"]) for key in manifest["models"]},
                        "slots": [{"slot_id": r["slot"]["slot_id"], "status": r["record"].get("status") if r["record"] else "not_recorded", "started_at": r["record"].get("execution_started_at") if r["record"] else None,
                                   "latency_seconds": (r["record"].get("harbor_metrics") or {}).get("agent_execution_seconds") if r["record"] else None,
                                   "provider_cost_delta_usd": r["record"].get("provider_cost_delta_usd") if r["record"] else None,
                                   "failure_categories": failure_categories(r["record"]),
                                   "errors": (r["record"].get("verdict") or {}).get("errors", []) if r["record"] else []} for r in rows]})
        lines += ["## " + manifest["stage"] + " - " + manifest["manifest_id"], "", "| Scope | Model | Financial / assessed | Evidence / assessed | Robustness / assessed | Verified / scheduled | Delivery / assessed | Strict / scheduled | Verdict coverage |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for row in table:
            cell = lambda key: str(row["components"][key]["passed"]) + " / " + str(row["components"][key]["assessed"])
            lines.append("| " + " | ".join((row["scope"], row["model_key"], cell("financial_answer"), cell("evidence"), cell("robustness"), f"{row['verified_research_completion']} / {row['scheduled']}", cell("delivery"), f"{row['strict_delivery_completion']} / {row['scheduled']}", f"{row['verdict_coverage']} / {row['scheduled']}")) + " |")
        lines += ["", "Balanced repetitions give equal weight to each task in the scheduled completion proportions. Component denominators count assessed verdicts. Missing or infrastructure-failed slots remain in scheduled denominators and are not fabricated model answers.", ""]
        lines += ["Latency, actual order, per-model cost deltas, unknown counts and nonexclusive failed components are retained in scores.json. Provider metadata can lag, so slot cost deltas are not exact model allocations. Native zero token fields do not establish zero usage.", ""]
        if showcase and showcase["primary"]:
            lines += ["Selected example: [" + showcase["primary"]["slot_id"] + "](" + showcase["primary"]["workpaper"].removeprefix("reports/challenge-v1/") + "). Selection: `" + showcase["selection_kind"] + "`.", ""]
            if showcase["contrast"]:
                lines += ["Passing contrast: [" + showcase["contrast"]["slot_id"] + "](" + showcase["contrast"]["workpaper"].removeprefix("reports/challenge-v1/") + ").", ""]
    lines += ["No assisted-condition trials are recorded. These small source groups and repeated attempts do not establish population reliability or a universal model ranking. Synthetic controls test a few declared mechanisms, not universal generalization.", ""]
    result = {"dataset_id": "challenge-v1", "studies": studies}
    reviewed = report_scoring_reviews(root)
    if reviewed is not None:
        result["scoring_reviews"] = reviewed
    (output / "scores.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "results.md").write_text("\n".join(lines))
    return result


def report_scoring_reviews(root):
    """Keep authenticated versioned scoring reviews separate from original records."""
    root = Path(root)
    bundle_path = root / "datasets/challenge-v1/scoring-review.json"
    if not bundle_path.is_file():
        return None
    bundle_bytes = bundle_path.read_bytes()
    bundle = json.loads(bundle_bytes)
    manifest_bytes = (root / "datasets/challenge-v1/manifests/evaluation.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if (bundle["original_manifest_sha256"] != hashlib.sha256(manifest_bytes).hexdigest()
            or bundle["original_manifest_id"] != manifest["manifest_id"]):
        raise ValueError("scoring_review_origin_mismatch")
    schedule = json.loads((root / manifest["schedule"]).read_text())
    slots = {slot["slot_id"]: slot for slot in schedule}
    indexes = root / "reports/challenge-v1/scoring-reviews" / bundle["review_id"]
    studies, pending = [], []
    lines = ["# Versioned evidence scoring review", "", "Original frozen verdicts remain unchanged. This separate review permits relevant NVIDIA income-statement support alongside a complete gross-profit bridge, Ripple's explicit May component schedule as an alternate May citation, Coinbase's direct derivatives/spot scope evidence, and Visa's aggregate inputs with lagged timing for its pricing identification limit. Related shared references are accepted while each claim still needs its own facts. Finance, calculation, delivery and source inputs stay fixed. Missing answers retain the scheduled denominator.", ""]

    def authenticated_bytes(path, expected):
        if (any(parent.is_symlink() for parent in (path, *path.parents) if parent.is_relative_to(root))
                or not path.is_file() or path.stat().st_size > 500_000):
            raise ValueError("unsafe_scoring_review_file")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("scoring_review_provenance_unverified")
        return data

    for index_path in sorted(indexes.glob("*/index.json")):
        audit_path = index_path.with_name("artifact-audit.json")
        if not audit_path.is_file():
            pending.append(index_path.relative_to(root).as_posix())
            continue
        audit = json.loads(audit_path.read_text())
        if audit.get("archive_digest_verified") is not True:
            raise ValueError("scoring_review_archive_unverified")
        hashes = audit["retained_file_sha256"]

        def imported(relative):
            path = root / relative
            if Path(relative).is_absolute() or ".." in Path(relative).parts or not path.resolve().is_relative_to(index_path.parent.resolve()):
                raise ValueError("scoring_review_path_outside_run")
            return authenticated_bytes(path, hashes.get(relative))

        index = json.loads(imported(index_path.relative_to(root).as_posix()))
        if index.get("input_source") != "retained_artifact":
            continue
        origin = audit["workflow_run"]
        if (index["review_id"] != bundle["review_id"] or index["manifest_id"] != manifest["manifest_id"]
                or index["scorer_version"] != bundle["scorer_version"]
                or str(index["run_id"]) != str(origin["id"])
                or index["commit_sha"] != origin["head_sha"]
                or str(index["run_attempt"]) != str(origin["run_attempt"])
                or index["scheduled"] != len(schedule)):
            raise ValueError("scoring_review_identity_mismatch")
        verdicts, changed, detail_changed = {}, [], []
        for relative in index["receipts"]:
            receipt = json.loads(imported(relative))
            identifier = receipt["slot_id"]
            if identifier not in slots or identifier in verdicts:
                raise ValueError("scoring_review_slot_mismatch")
            slot = slots[identifier]
            directory = root / "reports/runs" / manifest["manifest_id"] / identifier
            original_audit = json.loads(authenticated_bytes(
                directory / "artifact-audit.json", receipt["artifact_audit_sha256"]))
            if original_audit.get("archive_digest_verified") is not True:
                raise ValueError("scoring_review_original_unverified")
            original_hashes = original_audit["retained_file_sha256"]
            record_bytes = authenticated_bytes(directory / "record.json", original_hashes["record.json"])
            original = json.loads(record_bytes)["verdict"]
            if receipt["input_file"] not in ("answer.raw.txt", "answer.json"):
                raise ValueError("scoring_review_answer_path_invalid")
            answer_bytes = authenticated_bytes(directory / receipt["input_file"], original_hashes[receipt["input_file"]])
            prior_bytes = authenticated_bytes(directory / "verdict.json", original_hashes["verdict.json"])
            verifier_bytes = imported(receipt["verifier_path"])
            current = json.loads(verifier_bytes)
            if (receipt["review_id"] != bundle["review_id"]
                    or receipt["manifest_id"] != manifest["manifest_id"]
                    or receipt["manifest_sha256"] != hashlib.sha256(manifest_bytes).hexdigest()
                    or receipt["scorer_version"] != bundle["scorer_version"]
                    or receipt["run_id"] != index["run_id"]
                    or receipt["run_attempt"] != index["run_attempt"]
                    or receipt["commit_sha"] != index["commit_sha"]
                    or receipt["input_source"] != "retained_artifact"
                    or receipt["review_bundle_sha256"] != hashlib.sha256(bundle_bytes).hexdigest()
                    or receipt["record_sha256"] != hashlib.sha256(record_bytes).hexdigest()
                    or receipt["input_sha256"] != hashlib.sha256(answer_bytes).hexdigest()
                    or receipt["verifier_bytes_sha256"] != hashlib.sha256(verifier_bytes).hexdigest()
                    or receipt["prior_verdict_sha256"] != hashlib.sha256(prior_bytes).hexdigest()
                    or receipt["prior_verdict"] != json.loads(prior_bytes)
                    or receipt["prior_verdict"] != original or receipt["verdict"] != current
                    or current["scorer_version"] != bundle["scorer_version"]
                    or any(receipt[key] != slot[key] for key in ("model_key", "repetition", "split"))
                    or receipt["task_id"] != slot["task"]
                    or not all(current["isolation"].get(key) is True for key in
                               ("network_namespace_none", "network_probe_blocked", "no_inference_key", "no_docker_socket"))):
                raise ValueError("scoring_review_receipt_mismatch")
            if any(current["checks"][key] != original["checks"][key] for key in ("financial_answer", "robustness", "delivery")):
                raise ValueError("unexpected_non_evidence_scoring_change")
            if current["checks"] != original["checks"]:
                changed.append(identifier)
            if current.get("details") != original.get("details"):
                detail_changed.append(identifier)
            verdicts[identifier] = current
        missing_ids = set(slots) - set(verdicts)
        if (index["reviewed"] != len(verdicts)
                or len(index["missing_slots"]) != len(missing_ids)
                or {item["slot_id"] for item in index["missing_slots"]} != missing_ids):
            raise ValueError("scoring_review_coverage_mismatch")
        table = []
        for model in manifest["models"]:
            groups = [("all", [s for s in schedule if s["model_key"] == model])]
            groups += [(key, [s for s in schedule if s["model_key"] == model and s["task"] == task["task_id"]]) for key, task in manifest["tasks"].items()]
            groups += [("family-" + family, [s for s in schedule if s["model_key"] == model and s["task"].removeprefix("challenge-v1-").startswith(family.lower())]) for family in "ABC"]
            for scope, selected in groups:
                values = [verdicts[s["slot_id"]] for s in selected if s["slot_id"] in verdicts]
                components = {key: {"passed": sum(v["checks"][key] is True for v in values), "assessed": sum(isinstance(v["checks"][key], bool) for v in values)} for key in ("financial_answer", "evidence", "robustness", "delivery")}
                table.append({"scope": scope, "model_key": model, "scheduled": len(selected), "verdict_coverage": len(values), "components": components,
                              "verified_research_completion": sum(v["verified_research_completion"] is True for v in values), "strict_delivery_completion": sum(v["strict_delivery_completion"] is True for v in values)})
        study = {"review_id": bundle["review_id"], "scorer_version": bundle["scorer_version"], "manifest_id": manifest["manifest_id"], "run_id": index["run_id"], "metrics": table, "changed_component_slots": changed, "changed_detail_slots": detail_changed, "reviewed": len(verdicts), "scheduled": len(schedule), "missing_slots": sorted(set(slots) - set(verdicts))}
        study["task_macro_completion"] = {model: sum(row["verified_research_completion"] / row["scheduled"] for row in table if row["model_key"] == model and row["scope"] in manifest["tasks"]) / len(manifest["tasks"]) for model in manifest["models"]}
        studies.append(study)
        lines += ["## " + bundle["scorer_version"] + " - Actions " + str(index["run_id"]), "", "| Scope | Model | Financial / assessed | Evidence / assessed | Robustness / assessed | Verified / scheduled | Delivery / assessed | Strict / scheduled | Coverage |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for row in table:
            cell = lambda key: str(row["components"][key]["passed"]) + " / " + str(row["components"][key]["assessed"])
            lines.append("| " + " | ".join((row["scope"], row["model_key"], cell("financial_answer"), cell("evidence"), cell("robustness"), f"{row['verified_research_completion']} / {row['scheduled']}", cell("delivery"), f"{row['strict_delivery_completion']} / {row['scheduled']}", f"{row['verdict_coverage']} / {row['scheduled']}")) + " |")
        lines += ["", "Changed component slots: " + (", ".join(changed) or "none") + ".", ""]
        lines += ["Changed claim or conclusion details: " + (", ".join(detail_changed) or "none") + ". A corrected claim can leave overall evidence failure unchanged.", ""]
    result = {"studies": studies, "pending_authenticated_import": pending}
    output = root / "reports/challenge-v1"
    (output / "reviewed-results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "reviewed-results.md").write_text("\n".join(lines))
    return result
