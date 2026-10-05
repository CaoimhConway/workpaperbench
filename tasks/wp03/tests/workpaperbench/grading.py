"""Task-local evidence and reference checks. Replay only constrained SQL."""
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
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and abs(value - expected) <= tolerance


def evidence_ok(given, accepted):
    allowed = set().union(*(set(option) for option in accepted))
    return set(given) <= allowed and any(set(option) <= set(given) for option in accepted)


def grade(directory, trusted):
    trusted = Path(trusted)
    gold = json.loads((trusted / "gold.json").read_text())
    flags = {"format": False, "numerical": None, "evidence_context": False,
             "availability": False, "conclusion": None, "replay": None}
    errors = []
    for name in gold["hashes"]:
        if digest(trusted / name) != gold["hashes"][name]:
            return {"complete": False, "checks": flags, "errors": ["trusted_input_changed"]}
    try:
        answer = load_artifact(directory)
        validate(answer, json.loads((trusted / "schema.json").read_text()))
        claims = {a["id"]: a for a in answer["answers"]}
        if answer["task_id"] != gold["task_id"] or set(claims) != set(gold["answers"]):
            raise ValueError("claim_set")
        flags["format"] = True
    except Exception as exc:
        return {"complete": False, "checks": flags, "errors": ["format:" + type(exc).__name__]}
    numbers, citations, availability, queries = [], [], [], []
    for identifier, expected in gold["answers"].items():
        claim = claims[identifier]
        citation = evidence_ok(claim["evidence"], expected["evidence"])
        citations.append(citation)
        available = claim["status"] == expected["status"] and claim["unit"] == expected["unit"]
        if expected["status"] == "insufficient_evidence":
            available = available and claim["reason_code"] in expected["reason_codes"]
        else:
            numerical = claim["status"] == "answered" and close(claim["value"], expected["value"], expected["tolerance"])
            numbers.append(numerical)
            if claim["status"] == "answered":
                original = replay(claim["sql"], trusted / "data.sqlite")
                changed = replay(claim["sql"], trusted / "changed.sqlite")
                recomputed = close(original, expected["value"], expected["tolerance"]) and close(original, claim["value"], expected["tolerance"]) and close(changed, expected["changed_value"], expected["tolerance"])
            else:
                recomputed = False
            queries.append(recomputed)
            if not numerical:
                errors.append(identifier + ":numerical")
            if not recomputed:
                errors.append(identifier + ":replay")
        availability.append(available)
        if not citation:
            errors.append(identifier + ":evidence_context")
        if not available:
            errors.append(identifier + ":availability_or_unit")
    flags.update(numerical=all(numbers) if numbers else None, replay=all(queries) if queries else None,
                 evidence_context=all(citations), availability=all(availability))
    expected = gold["conclusion"]
    conclusion = answer["conclusion"]
    if expected is None:
        valid_conclusion = conclusion is None
    else:
        valid_conclusion = conclusion is not None and conclusion["verdict"] == expected["verdict"] and conclusion["reason_code"] in expected["reason_codes"] and evidence_ok(conclusion["evidence"], expected["evidence"])
        flags["conclusion"] = valid_conclusion
    if not valid_conclusion:
        errors.append("conclusion")
    return {"complete": all(v is not False for v in flags.values()) and valid_conclusion,
            "checks": flags, "errors": errors}
