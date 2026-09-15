"""Independent research, evidence, recomputation and delivery checks."""
import json
from pathlib import Path
import re
import subprocess
import sys

from .grading import aggregate, close, digest, load_artifact, parse, validate

SCORER_VERSION = "challenge-1.1.0"


def normalize_unit(unit):
    """Normalize ordinary spelling differences without converting units."""
    return re.sub(r"[\s_]+", "_", unit.strip()).casefold()


def support(given, accepted, context):
    allowed = set(context).union(*(set(option) for option in accepted))
    return set(given) <= allowed and any(set(option) <= set(given) for option in accepted)


def replay(sql, db):
    worker = Path(__file__).with_name("challenge_sql_worker.py").resolve()
    try:
        output = subprocess.run(
            [sys.executable, "-I", "-S", str(worker)],
            input=json.dumps({"db": str(Path(db).resolve()), "sql": sql}),
            text=True, capture_output=True, timeout=2, cwd=worker.parent,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        )
        value = json.loads(output.stdout)
        return value["value"] if output.returncode == 0 and set(value) == {"value"} else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def grade(directory, trusted):
    trusted = Path(trusted)
    gold = json.loads((trusted / "gold.json").read_text())
    checks = dict.fromkeys(("delivery", "financial_answer", "evidence", "robustness"))
    details = {"claims": {}, "conclusion": None}
    errors = []

    def result():
        verified = all(checks[key] is True for key in ("financial_answer", "evidence", "robustness"))
        strict = verified and checks["delivery"] is True
        return {"scorer_version": SCORER_VERSION, "complete": strict,
                "verified_research_completion": verified,
                "strict_delivery_completion": strict,
                "checks": checks, "details": details, "errors": errors}

    if any(digest(trusted / name) != value for name, value in gold["hashes"].items()):
        errors.append("trusted_input_changed")
        return result()
    try:
        answer = load_artifact(directory)
        validate(answer, json.loads((trusted / "schema.json").read_text()))
        if (answer["task_id"] != gold["task_id"]
                or len(answer["answers"]) != len(gold["answers"])
                or {a["id"] for a in answer["answers"]} != set(gold["answers"])):
            raise ValueError("claim_set")
        checks["delivery"] = True
    except Exception as exc:
        checks["delivery"] = False
        errors.append("delivery:" + type(exc).__name__)
        # Structural rejection never permits execution of submitted SQL.
        return result()

    shared = answer.get("context_evidence", [])
    shared_ok = set(shared) <= set(gold.get("context_evidence_allowed", []))
    finances, supports, calculations = [], [shared_ok], []
    for claim in answer["answers"]:
        identifier = claim["id"]
        expected = gold["answers"][identifier]
        item = {"availability": claim["status"] == expected["status"],
                "unit": normalize_unit(claim["unit"]) == normalize_unit(expected["unit"]),
                "evidence": support(claim["evidence"] + shared, expected["evidence"], gold.get("context_evidence_allowed", []))}
        if expected["status"] == "answered":
            item["numerical"] = close(claim["value"], expected["value"], expected["tolerance"])
            item["original_replay"] = close(replay(claim["sql"], trusted / "data.sqlite"),
                                               expected["value"], expected["tolerance"]) if item["availability"] else False
            item["controls"] = {}
            for control in gold["controls"]:
                item["controls"][control["name"]] = close(
                    replay(claim["sql"], trusted / control["database"]),
                    control["expected"][identifier], expected["tolerance"],
                ) if item["availability"] else False
            calculations.append(item["original_replay"] and all(item["controls"].values()))
            finances.append(item["numerical"] and item["availability"] and item["unit"])
        else:
            finances.append(item["availability"] and item["unit"])
        supports.append(item["evidence"])
        details["claims"][identifier] = item
        for key in ("availability", "unit", "numerical", "evidence", "original_replay"):
            if item.get(key) is False:
                errors.append(identifier + ":" + key)
        for name, passed in item.get("controls", {}).items():
            if not passed:
                errors.append(identifier + ":control:" + name)

    expected = gold.get("conclusion")
    conclusion = answer["conclusion"]
    if expected is None:
        finances.append(conclusion is None)
    elif isinstance(conclusion, dict):
        item = {"verdict": conclusion["verdict"] == expected["verdict"],
                "evidence": support(conclusion["evidence"] + shared, expected["evidence"], gold.get("context_evidence_allowed", []))}
        details["conclusion"] = item
        finances.append(item["verdict"])
        supports.append(item["evidence"])
        for key, passed in item.items():
            if not passed:
                errors.append("conclusion:" + key)
    else:
        finances.append(False)
        supports.append(False)
        errors.append("conclusion:missing")
    checks.update(financial_answer=aggregate(finances), evidence=aggregate(supports),
                  robustness=all(calculations) if calculations else None)
    return result()
