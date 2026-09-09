"""Versioned challenge unit matching and package selection."""
import copy
import hashlib
import importlib.util
import json
from decimal import Decimal
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_challenge_tasks as builder
import challenge_controls

SCORER_PATH = ROOT / "config/scorers/challenge-1.1.0.py"
spec = importlib.util.spec_from_file_location("workpaperbench.challenge_grading_110", SCORER_PATH)
scorer_110 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scorer_110
spec.loader.exec_module(scorer_110)


def definition(key="a01"):
    path = ROOT / "datasets/challenge-v1/authoring" / key / "definition.json"
    return json.loads(path.read_text())


def test_alias_control_varies_case_and_unit_separators():
    assert challenge_controls.alternate_unit_spelling("usd") == "USD"
    assert challenge_controls.alternate_unit_spelling("basis_points") == "BASIS POINTS"
    assert challenge_controls.alternate_unit_spelling("usd_million") == "USD MILLION"


def run_grade(tmp_path, monkeypatch, key, answer):
    task = ROOT / "datasets/challenge-v1/tasks" / key / "tests"
    reference = json.loads((task / "reference.json").read_text())
    gold = json.loads((task / "gold.json").read_text())
    identifiers = {claim["sql"]: claim["id"] for claim in reference["answers"] if claim["sql"]}
    original_values = {claim["id"]: claim["value"] for claim in reference["answers"]}

    def replay(sql, db):
        identifier = identifiers[sql]
        if db.name == "data.sqlite":
            return original_values[identifier]
        control = next(item for item in gold["controls"] if item["database"] == db.name)
        return control["expected"][identifier]

    monkeypatch.setattr(scorer_110, "replay", replay)
    (tmp_path / "answer.json").write_text(json.dumps(answer))
    return scorer_110.grade(tmp_path, task)


def test_unit_spelling_variants_are_accepted(tmp_path, monkeypatch):
    answer = copy.deepcopy(definition()["reference"])
    units = {claim["id"]: claim["unit"] for claim in answer["answers"]}
    units.update(eps_difference="USD per share", adjusted_operating_income="USD million",
                 margin_bridge="basis points")
    for claim in answer["answers"]:
        claim["unit"] = units[claim["id"]]
    verdict = run_grade(tmp_path, monkeypatch, "a01", answer)
    assert verdict["scorer_version"] == "challenge-1.1.0"
    assert verdict["checks"]["financial_answer"] is True
    assert verdict["details"]["claims"]["eps_difference"]["unit"] is True
    assert verdict["details"]["claims"]["adjusted_operating_income"]["unit"] is True
    assert verdict["details"]["claims"]["margin_bridge"]["unit"] is True

    reserve = copy.deepcopy(definition("b01")["reference"])
    for claim in reserve["answers"]:
        if claim["unit"] == "usd":
            claim["unit"] = "USD"
    reserve_verdict = run_grade(tmp_path, monkeypatch, "b01", reserve)
    assert reserve_verdict["details"]["claims"]["june_assets_usd"]["unit"] is True
    assert reserve_verdict["details"]["claims"]["coverage_change_pp"]["unit"] is True


def test_different_unit_and_incorrect_value_are_rejected(tmp_path, monkeypatch):
    answer = copy.deepcopy(definition()["reference"])
    claim = next(item for item in answer["answers"] if item["id"] == "adjusted_operating_income")
    claim["unit"] = "usd"
    verdict = run_grade(tmp_path, monkeypatch, "a01", answer)
    assert verdict["details"]["claims"]["adjusted_operating_income"]["unit"] is False
    assert verdict["checks"]["financial_answer"] is False

    answer = copy.deepcopy(definition("b01")["reference"])
    next(item for item in answer["answers"] if item["id"] == "june_assets_usd")["unit"] = "EUR"
    verdict = run_grade(tmp_path, monkeypatch, "b01", answer)
    assert verdict["details"]["claims"]["june_assets_usd"]["unit"] is False
    assert verdict["checks"]["financial_answer"] is False

    answer = copy.deepcopy(definition()["reference"])
    answer["answers"][0]["value"] += 0.1
    verdict = run_grade(tmp_path, monkeypatch, "a01", answer)
    assert verdict["details"]["claims"]["eps_difference"]["numerical"] is False
    assert verdict["checks"]["financial_answer"] is False


def test_structural_rejection_does_not_execute_sql(tmp_path, monkeypatch):
    answer = copy.deepcopy(definition()["reference"])
    answer["answers"].append(copy.deepcopy(answer["answers"][0]))
    answer["answers"][0]["sql"] = "DELETE FROM financials"
    (tmp_path / "answer.json").write_text(json.dumps(answer))
    monkeypatch.setattr(scorer_110, "replay", lambda *args: pytest.fail("SQL on structural rejection"))
    task = ROOT / "datasets/challenge-v1/tasks/a01/tests"
    verdict = scorer_110.grade(tmp_path, task)
    assert verdict["checks"]["delivery"] is False
    assert verdict["checks"]["robustness"] is None


def test_builder_gates_versioned_scorer_and_contract(tmp_path):
    old = definition()
    old_destination = tmp_path / "old"
    builder.package(old, old_destination)
    old_task = old_destination / "tasks/a01"
    old_tests = old_task / "tests"
    expected_old_task = ROOT / "datasets/challenge-v1/tasks/a01"
    old_files = {path.relative_to(old_task) for path in old_task.rglob("*") if path.is_file()}
    expected_old_files = {path.relative_to(expected_old_task)
                          for path in expected_old_task.rglob("*") if path.is_file()}
    assert old_files == expected_old_files
    old_gold = json.loads((old_tests / "gold.json").read_text())
    expected_gold_path = expected_old_task / "tests/gold.json"
    expected_gold = json.loads(expected_gold_path.read_text())
    actual_gold = copy.deepcopy(old_gold)
    actual_gold["hashes"] = expected_gold["hashes"]
    assert actual_gold == expected_gold
    for tests_dir, digests in ((old_tests, old_gold["hashes"]),
                               (expected_old_task / "tests", expected_gold["hashes"])):
        for name, digest in digests.items():
            assert hashlib.sha256((tests_dir / name).read_bytes()).hexdigest() == digest
    for relative in old_files:
        if relative == Path("tests/gold.json"):
            continue
        actual_path, expected_path = old_task / relative, expected_old_task / relative
        if relative.suffix == ".sqlite":
            assert builder.sqlite_contents(actual_path) == builder.sqlite_contents(expected_path)
        else:
            assert actual_path.read_bytes() == expected_path.read_bytes()
    assert "scorer_version" not in old_gold

    new = copy.deepcopy(old)
    new["scorer_version"] = "challenge-1.1.0"
    declared_tolerances = {
        "eps_difference": 0.125,
        "adjusted_operating_income": 0.25,
        "adjusted_margin": 0.5,
        "margin_bridge": 1.0,
    }
    for identifier, tolerance in declared_tolerances.items():
        new["gold"]["answers"][identifier]["tolerance"] = tolerance
    new_destination = tmp_path / "new"
    builder.package(new, new_destination)
    new_task = new_destination / "tasks/a01"
    new_tests = new_task / "tests"
    assert (new_tests / "workpaperbench/challenge_grading.py").read_bytes() == SCORER_PATH.read_bytes()
    new_gold = json.loads((new_tests / "gold.json").read_text())
    assert new_gold["scorer_version"] == "challenge-1.1.0"
    instruction = (new_task / "instruction.md").read_text()
    assert "All numeric tolerances are 0.000001" not in instruction
    tolerance_section = instruction.split(
        "Per-claim absolute numerical tolerances in requested units:\n", 1
    )[1].split("\nUse the public structure checker:", 1)[0]
    expected_lines = []
    for claim in new["reference"]["answers"]:
        expected = new["gold"]["answers"][claim["id"]]
        expected_lines.append(
            f"- {claim['id']}: {expected['unit']} - {format(Decimal(str(expected['tolerance'])), 'f')}"
        )
    assert tolerance_section == "\n".join(expected_lines)
    assert "runs of ordinary whitespace or underscores as a single underscore" in instruction

    unsupported = copy.deepcopy(old)
    unsupported["scorer_version"] = "challenge-2.0.0"
    with pytest.raises(ValueError, match="unsupported_challenge_scorer"):
        builder.package(unsupported, tmp_path / "unsupported")
