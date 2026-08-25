"""Versioned task grading with strict completion and independent diagnostics."""
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys

from jsonschema import Draft202012Validator

MAX_ARTIFACT = 65536
SCORER_VERSION = "1.1.0"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_key")
        result[key] = value
    return result


def parse(text):
    return json.loads(text, object_pairs_hook=unique_object,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite")))


def validate(answer, schema):
    Draft202012Validator(schema).validate(answer)
    for claim in answer["answers"]:
        if claim["status"] == "answered" and not math.isfinite(claim["value"]):
            raise ValueError("nonfinite")
    ids = [a["id"] for a in answer["answers"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate_claim")


def load_artifact(directory):
    directory = Path(directory)
    if directory.is_symlink():
        raise ValueError("artifact_directory_symlink")
    if sorted(p.name for p in directory.iterdir()) != ["answer.json"]:
        raise ValueError("unexpected_artifacts")
    fd = os.open(directory / "answer.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_ARTIFACT:
            raise ValueError("artifact_type_or_size")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            content = stream.read(MAX_ARTIFACT + 1)
        if len(content) > MAX_ARTIFACT:
            raise ValueError("artifact_size")
        return parse(content)
    finally:
        os.close(fd)


def replay(sql, db):
    worker = Path(__file__).with_name("sql_worker.py").resolve()
    try:
        result = subprocess.run([sys.executable, "-I", str(worker)],
                                input=json.dumps({"db": str(Path(db).resolve()), "sql": sql}),
                                text=True, capture_output=True, timeout=2,
                                cwd=worker.parent, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"})
        output = json.loads(result.stdout)
        if result.returncode or set(output) != {"value"}:
            return None
        return output["value"]
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return None


def close(value, expected, tolerance):
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (value, expected)) and abs(value - expected) <= tolerance


def evidence_ok(given, accepted):
    if not isinstance(given, list) or not all(isinstance(x, str) for x in given):
        return False
    allowed = set().union(*(set(option) for option in accepted))
    return set(given) <= allowed and any(set(option) <= set(given) for option in accepted)


def aggregate(values):
    """False means an observed failure. None means at least one check was not assessed."""
    if any(value is False for value in values):
        return False
    if not values or any(value is None for value in values):
        return None
    return True


def grade(directory, trusted):
    trusted = Path(trusted)
    gold = json.loads((trusted / "gold.json").read_text())
    flags = dict.fromkeys(("format", "numerical", "evidence_context", "availability", "conclusion", "replay"))
    details = {"claims": {}, "conclusion": None}
    errors = []

    def result(complete=False):
        return {"scorer_version": SCORER_VERSION, "complete": complete,
                "checks": flags, "details": details, "errors": errors}

    for name, expected_hash in gold["hashes"].items():
        if digest(trusted / name) != expected_hash:
            errors.append("trusted_input_changed")
            return result()
    try:
        answer = load_artifact(directory)
    except Exception as exc:
        flags["format"] = False
        errors.append("format:" + type(exc).__name__)
        return result()
    try:
        validate(answer, json.loads((trusted / "schema.json").read_text()))
        if answer["task_id"] != gold["task_id"] or {a["id"] for a in answer["answers"]} != set(gold["answers"]):
            raise ValueError("claim_set")
        flags["format"] = True
    except Exception as exc:
        flags["format"] = False
        errors.append("format:" + type(exc).__name__)

    # Observe uniquely identifiable requested claims even if an extra field/claim
    # made strict format fail. Never repair the submission or choose among duplicates.
    if not isinstance(answer, dict) or answer.get("task_id") != gold["task_id"] or not isinstance(answer.get("answers"), list):
        return result()
    if len(answer["answers"]) > 32:
        return result()
    numbers, citations, availability, queries = [], [], [], []
    for identifier, expected in gold["answers"].items():
        found = [a for a in answer["answers"] if isinstance(a, dict) and a.get("id") == identifier]
        item = dict.fromkeys(("numerical", "evidence", "availability", "unit", "reason_code", "original_replay", "changed_replay"))
        details["claims"][identifier] = item
        if len(found) != 1:
            citations.append(None)
            availability.append(None)
            if expected["status"] == "answered":
                numbers.append(None)
                queries.append(None)
            errors.append(identifier + ":not_assessed")
            continue
        claim = found[0]
        item["evidence"] = evidence_ok(claim.get("evidence"), expected["evidence"])
        item["availability"] = claim.get("status") == expected["status"]
        item["unit"] = claim.get("unit") == expected["unit"]
        available = item["availability"] and item["unit"]
        if expected["status"] == "insufficient_evidence":
            item["reason_code"] = claim.get("reason_code") in expected["reason_codes"]
            available = available and item["reason_code"]
        else:
            if claim.get("status") == "answered":
                item["numerical"] = close(claim.get("value"), expected["value"], expected["tolerance"])
                sql = claim.get("sql")
                if isinstance(sql, str) and len(sql.encode()) <= 16384:
                    original = replay(sql, trusted / "data.sqlite")
                    changed = replay(sql, trusted / "changed.sqlite")
                    item["original_replay"] = close(original, expected["value"], expected["tolerance"])
                    item["changed_replay"] = close(changed, expected["changed_value"], expected["tolerance"])
                    # Matching submitted value is also required, not only matching gold.
                    item["original_replay"] = item["original_replay"] and close(original, claim.get("value"), expected["tolerance"])
            numbers.append(item["numerical"])
            queries.append(aggregate([item["original_replay"], item["changed_replay"]]))
            if item["numerical"] is False:
                errors.append(identifier + ":numerical")
            if queries[-1] is not True:
                errors.append(identifier + ":replay")
        citations.append(item["evidence"])
        availability.append(available)
        if not item["evidence"]:
            errors.append(identifier + ":evidence_context")
        if not available:
            errors.append(identifier + ":availability_or_unit")
    flags.update(numerical=aggregate(numbers), replay=aggregate(queries),
                 evidence_context=aggregate(citations), availability=aggregate(availability))
    expected = gold["conclusion"]
    conclusion = answer.get("conclusion")
    if expected is None:
        valid_conclusion = conclusion is None
    else:
        if isinstance(conclusion, dict):
            details["conclusion"] = {
                "verdict": conclusion.get("verdict") == expected["verdict"],
                "reason_code": conclusion.get("reason_code") in expected["reason_codes"],
                "evidence": evidence_ok(conclusion.get("evidence"), expected["evidence"]),
            }
            valid_conclusion = all(details["conclusion"].values())
        else:
            valid_conclusion = False
        flags["conclusion"] = valid_conclusion
    if not valid_conclusion:
        errors.append("conclusion")
    required = [flags[name] for name in ("format", "evidence_context", "availability")]
    if numbers:
        required.extend([flags["numerical"], flags["replay"]])
    return result(all(value is True for value in required) and valid_conclusion)
