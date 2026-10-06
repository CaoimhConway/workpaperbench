"""Run one frozen WorkpaperBench slot through Harbor's native Hermes adapter."""
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = json.loads((ROOT / "config/runtime.json").read_text())
SLOT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
SAFE_TOOL_RE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
SAFE_ERROR_RE = re.compile(r"^[a-zA-Z0-9_.:-]{1,100}$")
SECRET_RE = re.compile(rb"sk-or-v1-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")
PROVIDER_CEILING_USD = 20.0
REAL_RUNTIME_INPUTS = {
    "config/runtime.json",
    "config/skills/contract-check/SKILL.md",
    "workpaperbench/grading.py",
    "workpaperbench/sql_worker.py",
    "scripts/native_run.py",
    "scripts/native_trial.py",
    "scripts/fix_native_version.py",
    "scripts/select_slots.py",
    "scripts/attempts.py",
    "scripts/build_real_tasks.py",
    "scripts/real_definitions.py",
}
CHALLENGE_RUNTIME_INPUTS = {
    "config/runtime.json",
    "workpaperbench/challenge_grading.py",
    "workpaperbench/challenge_sql_worker.py",
    "scripts/build_challenge_tasks.py",
    "scripts/native_run.py",
    "scripts/native_trial.py",
    "scripts/select_slots.py",
    "scripts/attempts.py",
    "scripts/collect_results.py",
    "scripts/fresh_replay.py",
    "scripts/check_install.py",
    "config/native-api-observer/plugin.yaml",
    "config/native-api-observer/__init__.py",
    ".github/workflows/benchmark.yml",
}
RETRY_LEDGER_MAX_BYTES = 65_536
RETRY_LEDGER_MAX_EVENTS = 256
RETRY_EVENT_KEYS = {
    "observer_registered": {"event", "observed_at"},
    "pre_api_request": {"event", "observed_at", "request_id", "api_call_count",
                         "retry_count", "max_retries", "started_at", "attempt_ordinal"},
    "post_api_request": {"event", "observed_at", "request_id", "api_call_count",
                         "retry_count", "max_retries", "started_at", "ended_at"},
    "api_request_error": {"event", "observed_at", "request_id", "api_call_count",
                           "retry_count", "max_retries", "started_at", "ended_at",
                           "http_status", "retryable"},
}


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, limit=8_000_000):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("unsafe_or_oversize_json")
    return json.loads(path.read_text())


def write_record(path, record):
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def list_slots(path):
    data = json.loads(path.read_text())
    if isinstance(data, dict):
        data = data.get("slots")
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("invalid_slot_manifest")
    return data


def frozen_inputs(manifest_id=None, root=None, *, reviewed_operations=False):
    root = ROOT if root is None else Path(root)
    selected = manifest_id or os.environ.get("WPB_MANIFEST_ID")
    if selected == "development-v1":
        raise ValueError("legacy_campaign_closed")
    if selected:
        from select_slots import campaign_context, campaign_slots
        context = campaign_context(selected, root)
        manifest = context["manifest"]
        if context["dataset_id"]:
            if context["dataset_id"] == "challenge-v1":
                campaign_slots(context, context["stage"])
            else:
                campaign_slots(context, "pilot")
                campaign_slots(context, "final")
    else:
        manifest = read_json(root / "config/freeze.json", 1_000_000)
    hashes = manifest.get("hashes")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("freeze_hashes_missing")
    if reviewed_operations and manifest.get("dataset_id") == "real-v1":
        from operations_review import reviewed_hashes
        hashes = reviewed_hashes(manifest, root)
    covered = set()
    for name, expected in hashes.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe_freeze_path")
        target = root
        for part in relative.parts:
            target = target / part
            if target.is_symlink():
                raise ValueError("freeze_input_symlink")
        if not target.is_file():
            raise ValueError("freeze_input_missing")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if not isinstance(expected, str) or actual != expected:
            raise ValueError("freeze_hash_mismatch")
        covered.add(relative.as_posix())
    if selected:
        if manifest.get("manifest_id") != selected and selected != "real-v1-development":
            raise ValueError("manifest_mismatch")
        if manifest.get("dataset_id") == "real-v1":
            from select_slots import real_dataset_context
            context = real_dataset_context(selected, root)
            required = {
                context["schedule_path"].relative_to(root).as_posix(),
                context["pilot_path"].relative_to(root).as_posix(),
                context["schema_path"].relative_to(root).as_posix(),
                *REAL_RUNTIME_INPUTS,
            }
            captures = root / "datasets/real-v1/captures"
            if captures.is_symlink() or not captures.is_dir():
                raise ValueError("freeze_capture_inputs_missing")
            for path in captures.rglob("*"):
                if path.is_symlink():
                    raise ValueError("freeze_input_symlink")
                if path.is_file():
                    required.add(path.relative_to(root).as_posix())
            for task in context["tasks"].values():
                task_path = root / task["path"]
                for path in task_path.rglob("*"):
                    if path.is_symlink():
                        raise ValueError("freeze_input_symlink")
                    if path.is_file():
                        required.add(path.relative_to(root).as_posix())
            if not required <= covered:
                raise ValueError("freeze_input_unlisted")
        elif manifest.get("dataset_id") == "challenge-v1":
            context = campaign_context(selected, root)
            required = {
                context["schedule_path"].relative_to(root).as_posix(),
                context["schema_path"].relative_to(root).as_posix(),
                *CHALLENGE_RUNTIME_INPUTS,
            }
            for task in context["tasks"].values():
                task_path = root / task["path"]
                for path in task_path.rglob("*"):
                    if path.is_symlink():
                        raise ValueError("freeze_input_symlink")
                    if path.is_file():
                        required.add(path.relative_to(root).as_posix())
            if not required <= covered:
                raise ValueError("freeze_input_unlisted")
    return manifest


def finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def credential_in(content, key):
    exact = key.encode("utf-8")
    variants = [exact, base64.b64encode(exact), exact.hex().encode()]
    fragments = [variant[i:i+16] for variant in variants for i in range(0, len(variant)-15, 8)]
    candidates = [content]
    try:
        candidates.append(json.dumps(json.loads(content), ensure_ascii=False).encode())
    except (ValueError, UnicodeError, RecursionError):
        pass
    # Also catch escaped credentials in incomplete or otherwise invalid JSON.
    candidates.append(re.sub(rb"\\u00([0-9a-fA-F]{2})", lambda m: bytes([int(m[1], 16)]), content))
    from urllib.parse import unquote_to_bytes
    candidates.append(unquote_to_bytes(content))
    for match in re.finditer(rb"[A-Za-z0-9+/]{24,}={0,2}|(?:[0-9a-fA-F]{2}){16,}", content):
        encoded = match[0]
        try:
            candidates.append(base64.b64decode(encoded, validate=True))
        except ValueError:
            pass
        if re.fullmatch(rb"(?:[0-9a-fA-F]{2}){16,}", encoded):
            candidates.append(bytes.fromhex(encoded.decode()))
    return any(SECRET_RE.search(c) or any(fragment in c for fragment in fragments) for c in candidates)


def provider_snapshot(key):
    request = Request(
        RUNTIME["cost"]["provider_metadata_url"],
        headers={"Authorization": "Bearer " + key, "Accept": "application/json"},
    )
    with urlopen(request, timeout=20) as response:
        data = json.load(response).get("data", {})
    credit_request = Request("https://openrouter.ai/api/v1/credits", headers={"Authorization": "Bearer " + key})
    with urlopen(credit_request, timeout=20) as response:
        credits = json.load(response).get("data", {})
    total_credit = finite_number(credits.get("total_credits"))
    total_usage = finite_number(credits.get("total_usage"))
    return {
        "lifetime_limit_usd": finite_number(data.get("limit")),
        "remaining_usd": finite_number(data.get("limit_remaining")),
        "usage_usd": finite_number(data.get("usage")),
        "funded_remaining_usd": total_credit - total_usage if total_credit is not None and total_usage is not None else None,
        "byok_usage_usd": finite_number(data.get("byok_usage")),
        "reset_is_null": "limit_reset" in data and data.get("limit_reset") is None,
        "includes_byok": data.get("include_byok_in_limit")
        if isinstance(data.get("include_byok_in_limit"), bool)
        else None,
    }


def all_records():
    for path in sorted((ROOT / "reports/runs").glob("**/record.json")):
        try:
            yield read_json(path, 300_000)
        except (OSError, ValueError, json.JSONDecodeError):
            continue


def final_reservation(schedule, records, manifest_id=None):
    base = float(RUNTIME["cost"]["reservation_usd_per_slot"])
    if manifest_id is not None:
        records = [item for item in records if item.get("experiment_id") == manifest_id
                   or item.get("dataset_manifest_id") == manifest_id]
    pilot_costs = [
        value
        for item in records
        if item.get("campaign") == "pilot"
        for value in [finite_number(item.get("provider_cost_delta_usd"))]
        if value is not None and value >= 0
    ]
    multiplier = float(RUNTIME["cost"]["pilot_cost_multiplier"])
    reserve = max(base, max(pilot_costs, default=0.0) * multiplier)
    by_id = {item.get("slot_id"): item for item in records}
    finished = {"complete", "task_failed", "infra_failed"}
    remaining = sum(
        by_id.get(slot.get("slot_id"), {}).get("status") not in finished
        for slot in schedule
    )
    return round(reserve, 8), remaining


def model_profile(context, slot):
    if context.get("dataset_id") == "challenge-v1":
        key = slot.get("model_key")
        profile = context["manifest"].get("models", {}).get(key)
        if not isinstance(profile, dict):
            raise ValueError("challenge_model_profile_missing")
        return profile
    return RUNTIME["model"]


def challenge_reservation(context, mode, current_slot, attempted, records):
    """Reserve each model's declared amount across the remaining unattempted schedule."""
    from select_slots import campaign_slots
    schedule = campaign_slots(context, mode)
    manifest_id = context["manifest_id"]
    relevant = [item for item in records
                if item.get("experiment_id") == manifest_id
                or item.get("dataset_manifest_id") == manifest_id]
    by_id = {item.get("slot_id"): item for item in relevant}
    remaining = []
    terminal = {"complete", "task_failed", "infra_failed", "blocked", "artifact_missing"}
    for slot in schedule:
        identifier = slot["slot_id"]
        if identifier != current_slot and identifier in attempted:
            continue
        prior = by_id.get(identifier)
        if identifier != current_slot and prior and prior.get("status") in terminal:
            continue
        remaining.append(slot)
    reserve = sum(float(model_profile(context, slot)["reservation_usd_per_slot"])
                  for slot in remaining)
    return round(reserve, 8), len(remaining)


def preflight(snapshot, reserve, remaining_slots):
    limit = snapshot.get("lifetime_limit_usd")
    remaining = snapshot.get("remaining_usd")
    funded = snapshot.get("funded_remaining_usd")
    byok = snapshot.get("byok_usage_usd")
    if limit is None or not 0 < limit <= PROVIDER_CEILING_USD:
        return "invalid_lifetime_limit"
    if not snapshot.get("reset_is_null"):
        return "provider_limit_must_be_lifetime"
    if byok is None or byok != 0:
        return "byok_usage_must_be_zero"
    required = round(reserve * max(1, remaining_slots), 8)
    if remaining is None or funded is None or min(remaining, funded) + 0.00000001 < required:
        return "insufficient_reserved_balance"
    return None


def bounded_bytes(path, limit):
    if not path.resolve().is_relative_to(ROOT / ".raw") or path.is_symlink() or not path.is_file():
        return None, "missing_or_symlink"
    info = path.stat()
    if info.st_size > limit:
        return None, "oversize"
    content = path.read_bytes()
    if len(content) > limit:
        return None, "oversize"
    return content, None


def retry_observer_evidence(path):
    """Retain only the observer's narrow metadata schema, never raw hook payloads."""
    limitations = "hooks_fail_open_upstream_internal_retries_and_routes_unobserved"

    def empty(status, *, possibly_truncated=False):
        return {"capture_status": status, "capture_completeness": "not_guaranteed",
                "capture_limitations": limitations,
                "capture_truncated_possible": possibly_truncated,
                "observer_registered": False, "event_count": 0,
                "pre_request_count": 0, "observed_additional_attempts": 0, "events": []}

    content, reason = bounded_bytes(path, RETRY_LEDGER_MAX_BYTES)
    if reason:
        status = "missing" if reason == "missing_or_symlink" and not path.exists() else reason
        return empty(status)
    try:
        rows = [json.loads(line) for line in content.decode("utf-8").splitlines()]
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        rows = None
    if (not isinstance(rows, list) or not rows or len(rows) > RETRY_LEDGER_MAX_EVENTS
            or any(not isinstance(row, dict) for row in rows)):
        status = "event_limit_reached" if isinstance(rows, list) and len(rows) > RETRY_LEDGER_MAX_EVENTS else "invalid"
        return empty(status, possibly_truncated=status == "event_limit_reached")

    events = []
    attempts_by_request = {}
    additional = 0
    for row in rows:
        event = row.get("event")
        if not isinstance(event, str) or event not in RETRY_EVENT_KEYS or set(row) != RETRY_EVENT_KEYS[event]:
            events = None
            break
        observed_at = finite_number(row.get("observed_at"))
        if observed_at is None or observed_at <= 0:
            events = None
            break
        clean = {"event": event, "observed_at": observed_at}
        if event != "observer_registered":
            request_id = row.get("request_id")
            if request_id is not None and not re.fullmatch(r"[0-9a-f]{64}", str(request_id)):
                events = None
                break
            clean["request_id"] = request_id
            for name in ("api_call_count", "retry_count", "max_retries"):
                value = row.get(name)
                if value is not None and (isinstance(value, bool) or not isinstance(value, int)
                                          or not 0 <= value <= 1_000_000_000):
                    events = None
                    break
                clean[name] = value
            if events is None:
                break
            for name in ("started_at", "ended_at"):
                if name in row:
                    value = finite_number(row[name])
                    if row[name] is not None and (value is None or not 0 < value < 10_000_000_000):
                        events = None
                        break
                    clean[name] = value
            if events is None:
                break
            if event == "pre_api_request":
                ordinal = row.get("attempt_ordinal")
                if ordinal is not None and (isinstance(ordinal, bool) or not isinstance(ordinal, int)
                                            or not 1 <= ordinal <= RETRY_LEDGER_MAX_EVENTS):
                    events = None
                    break
                if request_id is not None:
                    expected = attempts_by_request.get(request_id, 0) + 1
                    if ordinal != expected:
                        events = None
                        break
                    attempts_by_request[request_id] = expected
                    if expected > 1:
                        additional += 1
                elif ordinal is not None:
                    events = None
                    break
                clean["attempt_ordinal"] = ordinal
            elif event == "api_request_error":
                status = row.get("http_status")
                retryable = row.get("retryable")
                if status is not None and (isinstance(status, bool) or not isinstance(status, int)
                                           or not 100 <= status <= 599):
                    events = None
                    break
                if retryable is not None and not isinstance(retryable, bool):
                    events = None
                    break
                clean["http_status"] = status
                clean["retryable"] = retryable
        events.append(clean)
    if events is None:
        return empty("invalid")
    pre_count = sum(event["event"] == "pre_api_request" for event in events)
    registered = any(e["event"] == "observer_registered" for e in events)
    hooks_observed = any(e["event"] != "observer_registered" for e in events)
    possibly_truncated = len(rows) >= RETRY_LEDGER_MAX_EVENTS or len(content) >= RETRY_LEDGER_MAX_BYTES - 512
    status = ("event_limit_reached" if len(rows) >= RETRY_LEDGER_MAX_EVENTS else
              "size_limit_near" if len(content) >= RETRY_LEDGER_MAX_BYTES - 512 else
              "captured" if registered or hooks_observed else "registration_not_observed")
    return {"capture_status": status, "capture_completeness": "not_guaranteed",
            "capture_limitations": limitations,
            "capture_truncated_possible": possibly_truncated,
            "observer_registered": registered or hooks_observed,
            "event_count": len(events), "pre_request_count": pre_count,
            "observed_additional_attempts": additional, "events": events}


def sanitized_verdict(path):
    content, reason = bounded_bytes(path, 100_000)
    if reason:
        return None
    try:
        value = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    result = {"complete": value.get("complete") is True}
    checks = value.get("checks")
    result["checks"] = {
        key: state
        for key, state in checks.items()
        if isinstance(checks, dict)
        and isinstance(key, str)
        and re.fullmatch(r"[a-z0-9_]{1,60}", key)
        and (isinstance(state, bool) or state is None)
    } if isinstance(checks, dict) else {}
    errors = value.get("errors")
    result["errors"] = [
        item[:100]
        for item in errors[:50]
        if isinstance(item, str) and SAFE_ERROR_RE.fullmatch(item)
    ] if isinstance(errors, list) else []
    isolation = value.get("isolation")
    result["isolation"] = {
        key: state
        for key, state in isolation.items()
        if isinstance(isolation, dict)
        and key in {"network_probe_blocked", "network_namespace_none", "no_inference_key", "no_docker_socket"}
        and isinstance(state, bool)
    } if isinstance(isolation, dict) else {}
    if isinstance(value.get("verified_research_completion"), bool):
        result["verified_research_completion"] = value["verified_research_completion"]
    if isinstance(value.get("strict_delivery_completion"), bool):
        result["strict_delivery_completion"] = value["strict_delivery_completion"]
    if isinstance(value.get("scorer_version"), str) and re.fullmatch(r"[A-Za-z0-9._-]{1,40}", value["scorer_version"]):
        result["scorer_version"] = value["scorer_version"]
    detail = value.get("details")
    if isinstance(detail, dict):
        def safe_detail(item, depth=0):
            if depth > 5:
                return None
            if item is None or isinstance(item, bool):
                return item
            if isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(item):
                return item
            if isinstance(item, str):
                return item[:100] if re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", item) else None
            if isinstance(item, list):
                return [safe_detail(value, depth + 1) for value in item[:100]]
            if isinstance(item, dict):
                return {key: safe_detail(value, depth + 1)
                        for key, value in list(item.items())[:100]
                        if isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", key)}
            return None
        result["details"] = safe_detail(detail)
    return result


def tool_counts(path, key=None):
    try:
        trajectory = read_json(path, 5_000_000)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    counts = {}
    for step in trajectory.get("steps", []) if isinstance(trajectory, dict) else []:
        for call in step.get("tool_calls", []) if isinstance(step, dict) else []:
            name = call.get("function_name") if isinstance(call, dict) else None
            if isinstance(name, str) and SAFE_TOOL_RE.fullmatch(name) and not (key and credential_in(name.encode(), key)):
                counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items())[:50])


def save_tool_evidence(path, destination, key):
    try:
        trajectory = read_json(path, 5_000_000)
    except (OSError, ValueError):
        return {"status": "unavailable", "calls": 0}
    calls, observations, omitted = [], [], 0
    for step in trajectory.get("steps", []):
        for call in step.get("tool_calls", []) if isinstance(step, dict) else []:
            if not isinstance(call, dict):
                continue
            item = {k: call[k] for k in ("function_name", "arguments", "tool_call_id") if k in call}
            payload = json.dumps(item).encode()
            if len(calls) >= 25 or len(payload) > 8000 or credential_in(payload, key):
                omitted += 1
                continue
            calls.append(item)
        observation = step.get("observation", {}) if isinstance(step, dict) else {}
        for result in observation.get("results", []) if isinstance(observation, dict) else []:
            if not isinstance(result, dict):
                continue
            item = {k: result[k] for k in ("source_call_id", "content") if k in result}
            payload = json.dumps(item).encode()
            if len(observations) >= 25 or len(payload) > 8000 or credential_in(payload, key):
                omitted += 1
                continue
            observations.append(item)
    data = {"calls": calls, "observations": observations, "omitted_items": omitted,
            "scope": "Bounded screened tool invocations and observations only. No assistant messages, private reasoning or claim of complete trajectories. Omitted items may exceed bounds or contain credential patterns."}
    destination.write_text(json.dumps(data, indent=2) + "\n")
    return {"status": "screened_tools", "calls": len(calls), "observations": len(observations), "omitted_items": omitted}


def failure_codes(path):
    content, reason = bounded_bytes(path, 1_000_000)
    if reason:
        return []
    text = content.decode("utf-8", errors="replace").lower()
    markers = {
        "invalid_model_id": ("not a valid model", "model not found", "invalid model"),
        "missing_provider_key": ("no api key", "no provider configured"),
        "unsupported_cli_arguments": ("unrecognized arguments", "unknown option"),
        "runtime_import_failure": ("importerror", "modulenotfounderror"),
        "noninteractive_model_guard": ("refusing this startup model override",),
        "provider_authentication": ("unauthorized", "authenticationerror"),
        "provider_rate_limit": ("ratelimiterror", "rate limit exceeded"),
    }
    return [code for code, phrases in markers.items() if any(phrase in text for phrase in phrases)]


def result_metrics(path):
    try:
        result = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None, None
    context = result.get("agent_result") or {}
    metrics = {}
    for phase in ("environment_setup", "agent_setup", "agent_execution", "verifier"):
        timing = result.get(phase) or {}
        try:
            seconds = (datetime.fromisoformat(timing["finished_at"]) - datetime.fromisoformat(timing["started_at"])).total_seconds()
            if seconds >= 0:
                metrics[phase + "_seconds"] = round(seconds, 3)
        except (KeyError, TypeError, ValueError):
            metrics[phase + "_seconds"] = None
    for field in ("n_input_tokens", "n_cache_tokens", "n_output_tokens"):
        value = context.get(field)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            metrics[field] = value
    for field in ("cost_usd",):
        value = finite_number(context.get(field))
        if value is not None and value >= 0:
            metrics[field] = value
    exception = result.get("exception_info")
    exception_type = None
    if isinstance(exception, dict):
        raw_type = exception.get("exception_type")
        if isinstance(raw_type, str) and SAFE_TOOL_RE.fullmatch(raw_type):
            exception_type = raw_type
    return metrics, exception_type


def check_treatment(slot, config_path):
    if slot.get("arm") != "B":
        return None
    skill_dir = ROOT / RUNTIME["agent"]["treatment_skill_dir"]
    skill_file = skill_dir / "SKILL.md"
    if skill_dir.is_symlink() or skill_file.is_symlink() or not skill_file.is_file():
        raise ValueError("treatment_skill_missing")
    content = skill_file.read_text()
    words = re.findall(r"\b[\w'-]+\b", content)
    if not 150 <= len(words) <= 300:
        raise ValueError("treatment_skill_word_count")
    data = {
        "extra_instruction_paths": [str(skill_file.resolve())],
        "agent": {"skills": [str(skill_dir.resolve())]},
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2) + "\n")
    return {"word_count": len(words), "delivery": ["extra_instruction_paths", "agent.skills"]}


def validate_live_environment():
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("RUNNER_OS") != "Linux"
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
            or os.environ.get("GITHUB_REF") != "refs/heads/main"):
        raise ValueError("live_slots_require_dedicated_default_branch_actions")
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise ValueError("missing_openrouter_key")


def clean_process_env(key):
    allowed = ("PATH", "HOME", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL",
               "GITHUB_ACTIONS", "RUNNER_OS", "GITHUB_REPOSITORY", "GITHUB_REF")
    result = {name: os.environ[name] for name in allowed if name in os.environ}
    result["OPENROUTER_API_KEY"] = key
    result["PYTHONUNBUFFERED"] = "1"
    result["NO_COLOR"] = "1"
    return result


def execute(mode, slot_id):
    validate_live_environment()
    if mode not in {"pilot", "final"} or not SLOT_RE.fullmatch(slot_id):
        raise ValueError("invalid_mode_or_slot_id")
    from select_slots import campaign_context, campaign_slots
    manifest_id = os.environ["WPB_MANIFEST_ID"]
    context = campaign_context(manifest_id, ROOT)
    if context["dataset_id"] == "real-v1" and (
            (mode == "pilot" and manifest_id != "real-v1-development")
            or (mode == "final" and manifest_id != context["manifest_id"])):
        raise ValueError("manifest_campaign_mismatch")
    if context["dataset_id"] == "challenge-v1" and mode != context.get("stage"):
        raise ValueError("manifest_campaign_mismatch")
    if context["dataset_id"] == "challenge-v1" and os.environ.get("WPB_BATCH") != "all":
        raise ValueError("challenge_requires_batch_all")
    slots = campaign_slots(context, mode)
    matches = [slot for slot in slots if slot.get("slot_id") == slot_id]
    if len(matches) != 1:
        raise ValueError("slot_not_unique_in_manifest")
    slot = matches[0]
    if slot.get("campaign") != mode:
        raise ValueError("slot_campaign_mismatch")
    task_id = slot.get("task")
    task_metadata = None
    challenge = context["dataset_id"] == "challenge-v1"
    if challenge:
        task_key = task_id.removeprefix("challenge-v1-") if isinstance(task_id, str) else ""
        task_metadata = context["tasks"].get(task_key)
        task_dir = ROOT / task_metadata["path"] if task_metadata else ROOT / "datasets/challenge-v1/tasks/missing"
    elif context["dataset_id"]:
        task_key = task_id.removeprefix("real-v1-") if isinstance(task_id, str) else ""
        task_metadata = context["tasks"].get(task_key)
        task_dir = ROOT / task_metadata["path"] if task_metadata else ROOT / "datasets/real-v1/tasks/missing"
    else:
        if not isinstance(task_id, str) or not re.fullmatch(r"wp[0-9]{2}", task_id):
            raise ValueError("invalid_task_id")
        task_dir = ROOT / "tasks" / task_id
    if not task_dir.is_dir() or task_dir.is_symlink():
        raise ValueError("task_directory_missing")

    from attempts import check, record_directory
    if mode == "pilot" and context["dataset_id"] is None:
        raise ValueError("pilot_manifest_mismatch")
    output_dir = record_directory(manifest_id, slot_id)
    for directory in (ROOT / "reports", ROOT / "reports/runs", output_dir):
        if directory.exists() and (directory.is_symlink() or not directory.is_dir()):
            raise ValueError("unsafe_output_path")
    output_dir.mkdir(parents=True, exist_ok=True)
    record_path = output_dir / "record.json"
    prior = read_json(record_path, 300_000) if record_path.is_file() else None
    if record_path.is_symlink() or (prior is not None and not (
        prior.get("status") == "setup_started"
        and str(prior.get("run_id")) == os.environ.get("GITHUB_RUN_ID")
        and str(prior.get("github_run_attempt")) == "1"
    )):
        raise ValueError("slot_record_already_exists")
    if prior is None:
        raise ValueError("attempt_receipt_missing")
    if os.environ.get("GITHUB_RUN_ATTEMPT") != "1":
        raise ValueError("same_run_retry_disabled")

    attempted = check(mode, manifest_id, [slot_id])
    profile = model_profile(context, slot)
    record = {
        "experiment_id": manifest_id,
        "campaign": slot["campaign"],
        "task": task_id,
        "arm": slot.get("arm"),
        "repetition": slot.get("repetition"),
        "slot_id": slot_id,
        "split": slot.get("split"),
        "status": "started",
        "started_at": prior["started_at"] if prior else now(),
        "execution_started_at": now(),
        "remaining_planned_slots": prior.get("remaining_planned_slots"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "commit_sha": os.environ.get("GITHUB_SHA"),
        "harbor_version": RUNTIME["harbor"]["version"],
        "harbor_commit": RUNTIME["harbor"]["git_commit"],
        "harbor_native_version_fix": RUNTIME["harbor"].get("native_version_fix"),
        "hermes_release_tag": RUNTIME["hermes"]["release_tag"],
        "hermes_resolved_release_commit": RUNTIME["hermes"]["resolved_release_commit"],
        "hermes_checkout_commit_verified": False,
        "model": profile["id"],
        "model_route_policy": profile["route_policy"],
        "reservation_usd_per_slot": float(profile.get(
        "reservation_usd_per_slot", RUNTIME["cost"]["reservation_usd_per_slot"])),
    }
    if challenge:
        record.update(model_key=slot["model_key"], condition=slot["condition"],
                      model_provider=profile["provider"],
                      model_harbor_model=profile["harbor_model"])
    if task_metadata:
        record["dataset_id"] = context["dataset_id"]
        record["dataset_manifest_id"] = context["manifest_id"]
        record["source_group"] = task_metadata["source_group"]
        record["task_origin"] = task_metadata["origin"]
        record["previously_exposed"] = task_metadata.get("previously_exposed")
    else:
        definition = json.loads((ROOT / "sources" / (task_id + ".json")).read_text())
        record["source_group"] = definition["source_group"]
        record["task_origin"] = definition["origin"]
    config_payload = ((ROOT / "config/runtime.json").read_bytes()
                      + (task_dir / "task.toml").read_bytes()
                      + (task_dir / "instruction.md").read_bytes())
    if challenge:
        config_payload += json.dumps(profile, sort_keys=True, separators=(",", ":")).encode()
        config_payload += context["schema_path"].read_bytes()
        config_payload += str(slot.get("condition")).encode()
    record["config_hash"] = hashlib.sha256(config_payload).hexdigest()
    try:
        freeze = frozen_inputs(manifest_id)
        if context["dataset_id"]:
            record["dataset_manifest_id"] = freeze["manifest_id"]
            record["dataset_hash_count"] = len(freeze["hashes"])
        if mode == "final":
            record["freeze_manifest_id"] = freeze.get("manifest_id")
            record["freeze_hash_count"] = len(freeze["hashes"])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        record.update(status="blocked", reason_code=str(exc))
        record["finished_at"] = now()
        write_record(record_path, record)
        return record
    write_record(record_path, record)

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        record.update(status="blocked", reason_code="missing_openrouter_key", finished_at=now())
        write_record(record_path, record)
        return record
    try:
        before = provider_snapshot(key)
    except (OSError, ValueError, URLError, json.JSONDecodeError):
        record.update(status="blocked", reason_code="provider_metadata_unavailable", finished_at=now())
        write_record(record_path, record)
        return record
    record["provider_before"] = before
    schedule = slots if mode == "final" else []
    if challenge:
        reserved, remaining_slots = challenge_reservation(
            context, mode, slot_id, attempted, list(all_records()))
        record["remaining_reserved_usd"] = reserved
        record["remaining_reserved_slots"] = remaining_slots
        reason = preflight(before, reserved, 1)
    elif mode == "final":
        reserve, _ = final_reservation(schedule, list(all_records()), manifest_id)
        remaining_slots = prior.get("remaining_planned_slots")
        if isinstance(remaining_slots, bool) or not isinstance(remaining_slots, int) or not 1 <= remaining_slots <= len(schedule):
            raise ValueError("remaining_reservation_receipt_missing")
        record["reservation_usd_per_slot"] = reserve
        reason = preflight(before, reserve, remaining_slots)
    else:
        reserve = float(RUNTIME["cost"]["reservation_usd_per_slot"])
        record["reservation_usd_per_slot"] = reserve
        reason = preflight(before, reserve, 1)
    if reason:
        record.update(status="blocked", reason_code=reason, finished_at=now())
        write_record(record_path, record)
        return record

    harbor = shutil.which("harbor")
    raw_root = ROOT / ".raw/harbor"
    native_trial_name = f"{manifest_id[-12:]}-{slot_id}" if challenge else slot_id
    trial_dir = raw_root / native_trial_name
    if harbor is None or trial_dir.exists() or trial_dir.is_symlink():
        record.update(status="infra_failed", reason_code="harbor_missing_or_trial_exists", finished_at=now())
        write_record(record_path, record)
        return record
    config_path = ROOT / ".raw/configs" / (native_trial_name + ".json")
    try:
        treatment = check_treatment(slot, config_path)
    except (OSError, ValueError) as exc:
        record.update(status="blocked", reason_code=str(exc), finished_at=now())
        write_record(record_path, record)
        return record
    if treatment:
        record["treatment"] = treatment

    trial_config = {"task": {"path": str(task_dir)}, "trial_name": native_trial_name,
                    "trials_dir": str(raw_root), "agent": {
                        "name": "hermes", "model_name": profile["harbor_model"],
                        "env": {"HERMES_HOME": "/tmp/hermes"},
                        "kwargs": {"version": RUNTIME["hermes"]["release_tag"],
                                   "toolsets": RUNTIME["agent"]["toolsets"]},
                        "override_timeout_sec": RUNTIME["agent"]["solve_timeout_sec"],
                        "override_setup_timeout_sec": RUNTIME["agent"]["setup_timeout_sec"]}}
    if challenge:
        trial_config["agent"]["env"]["WPB_NATIVE_RETRY_LEDGER"] = "/logs/agent/native-api-observer.jsonl"
    if treatment:
        injected = json.loads(config_path.read_text())
        trial_config["extra_instruction_paths"] = injected["extra_instruction_paths"]
        trial_config["agent"]["skills"] = injected["agent"]["skills"]
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(trial_config, indent=2) + "\n")
    command = [sys.executable, str(ROOT / "scripts/native_trial.py"), str(config_path)]
    raw_root.mkdir(parents=True, exist_ok=True)
    raw_log = ROOT / ".raw/logs" / (native_trial_name + ".log")
    raw_log.parent.mkdir(parents=True, exist_ok=True)
    record["native_command"] = "Harbor Trial.create / Trial.run with native Hermes"
    write_record(record_path, record)
    try:
        with raw_log.open("wb") as log:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=clean_process_env(key),
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=3600,
                check=False,
            )
        record["native_return_code"] = completed.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        record["native_exception_type"] = type(exc).__name__
        record["native_return_code"] = None

    result_path = trial_dir / "result.json"
    version_path = ROOT / ".raw/versions" / (native_trial_name + ".json")
    if version_path.is_file():
        version = read_json(version_path, 2000)
        record["hermes_runtime_version"] = version
        record["hermes_checkout_commit_verified"] = version.get("matches_pin") is True
    metrics, exception_type = result_metrics(result_path)
    record["harbor_metrics"] = metrics
    if challenge:
        record["native_api_retry_observer"] = retry_observer_evidence(
            trial_dir / "agent/native-api-observer.jsonl")
    if exception_type:
        record["native_exception_type"] = exception_type
        record["native_failure_codes"] = failure_codes(trial_dir / "agent/hermes.txt")
    record["tool_event_counts"] = tool_counts(trial_dir / "agent/trajectory.json", key)
    record["tool_evidence"] = save_tool_evidence(trial_dir / "agent/trajectory.json", output_dir / "tool-evidence.json", key)

    answer_path = trial_dir / "artifacts/logs/artifacts/answer.json"
    answer, answer_error = bounded_bytes(answer_path, int(RUNTIME["max_answer_bytes"]))
    if answer is not None:
        if credential_in(answer, key):
            answer_error = "credential_pattern"
            record["raw_artifact_status"] = "withheld_credential_pattern"
        else:
            record["raw_sha256"] = hashlib.sha256(answer).hexdigest()
            record["raw_artifact_status"] = "screened_original_bytes"
            (output_dir / "answer.raw.txt").write_bytes(answer)
            try:
                if challenge:
                    from workpaperbench.challenge_grading import parse, validate
                else:
                    from workpaperbench.grading import parse, validate
                parsed = parse(answer)
                validate(parsed, json.loads(context["schema_path"].read_text()))
                canonical = (json.dumps(parsed, indent=2) + "\n").encode()
                if credential_in(canonical, key):
                    answer_error = "credential_pattern"
                else:
                    (output_dir / "answer.json").write_bytes(canonical)
                    record["retained_sha256"] = hashlib.sha256(canonical).hexdigest()
                    record["answer_sha256"] = record["retained_sha256"]
            except Exception:
                answer_error = "invalid_structure_original_retained"
    record["answer_status"] = "saved" if answer is not None and answer_error is None else answer_error

    verdict = sanitized_verdict(trial_dir / "verifier/verdict.json")
    if verdict is not None:
        record["verdict"] = verdict
        (output_dir / "verdict.json").write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    else:
        record["verdict"] = None

    try:
        after = provider_snapshot(key)
        record["provider_after"] = after
        start_usage = before.get("usage_usd")
        end_usage = after.get("usage_usd")
        if start_usage is not None and end_usage is not None and end_usage >= start_usage:
            record["provider_cost_delta_usd"] = round(end_usage - start_usage, 8)
        else:
            record["provider_cost_delta_usd"] = None
    except (OSError, ValueError, URLError, json.JSONDecodeError):
        record["provider_after"] = None
        record["provider_cost_delta_usd"] = None
    tokens = [metrics.get(name) for name in ("n_input_tokens", "n_output_tokens")] if metrics else []
    record["token_counts_status"] = "native_reported_positive" if any(value and value > 0 for value in tokens) else "unreported_or_native_zero_fields"
    return_code = record.get("native_return_code")
    if return_code != 0 or record.get("native_exception_type") or verdict is None:
        record["status"] = "infra_failed"
    else:
        record["status"] = "complete" if verdict.get("complete") else "task_failed"
    record["finished_at"] = now()
    write_record(record_path, record)
    return record


def main():
    if len(sys.argv) != 3:
        print("usage: python scripts/native_run.py MODE SLOT_ID")
        return 2
    try:
        record = execute(sys.argv[1], sys.argv[2])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("slot runner failed: " + str(exc))
        return 2
    print(record["slot_id"] + " " + record["status"])
    return 0 if record["status"] in {"complete", "task_failed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
