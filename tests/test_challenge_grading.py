"""Research scoring gates and independently recomputed dossier references."""
import copy
from decimal import Decimal
import json
from pathlib import Path

import pytest

from workpaperbench import challenge_grading as scorer

ROOT = Path(__file__).resolve().parents[1]


def definition(key):
    return json.loads((ROOT / "datasets/challenge-v1/authoring" / key / "definition.json").read_text())


def test_independent_source_arithmetic():
    adobe = definition("a01")
    values = {r[2]: Decimal(str(r[4])) for r in adobe["tables"]["financials"]["rows"] if r[:2] == ["2024-11-29", 3]}
    bridge = sum(Decimal(str(r[3])) for r in adobe["tables"]["adjustments"]["rows"] if r[:2] == ["2024-11-29", 3])
    assert bridge == 639
    assert values["GAAP operating income"] + bridge == 2596
    expected = {a["id"]: Decimal(str(a["value"])) for a in adobe["reference"]["answers"]}
    assert abs(expected["adjusted_margin"] - Decimal(259600) / 5606) < Decimal(".000001")
    assert abs(expected["margin_bridge"] - Decimal(6390000) / 5606) < Decimal(".000001")
    assert expected["eps_difference"] == Decimal(".13")
    paypal = definition("c01")
    expected = {a["id"]: Decimal(str(a["value"])) for a in paypal["reference"]["answers"]}
    assert abs(expected["yield_2024"] - Decimal(2884200) / 1681150) < Decimal(".000001")
    assert abs(expected["yield_2023"] - Decimal(2685700) / 1528579) < Decimal(".000001")
    assert abs(expected["transaction_contribution"] - Decimal(198500) / 2026) < Decimal(".000001")
    reserve = definition("b01")
    for row in reserve["tables"]["reserve_reports"]["rows"]:
        assert row[5] + row[6] == row[7] == row[4]
    assert all(e["publication"] == "unknown" for e in reserve["evidence"])


def test_rejected_structure_never_executes_sql(tmp_path, monkeypatch):
    ref = definition("a01")["reference"]
    ref["answers"].append(copy.deepcopy(ref["answers"][0]))
    ref["answers"][0]["sql"] = "DELETE FROM financials"
    (tmp_path / "answer.json").write_text(json.dumps(ref))
    monkeypatch.setattr(scorer, "replay", lambda *args: pytest.fail("SQL on structural rejection"))
    verdict = scorer.grade(tmp_path, ROOT / "datasets/challenge-v1/tasks/a01/tests")
    assert verdict["checks"]["delivery"] is False
    assert verdict["checks"]["robustness"] is None
    assert verdict["verified_research_completion"] is False


def test_every_financial_quantity_is_required(tmp_path, monkeypatch):
    task = ROOT / "datasets/challenge-v1/tasks/a01/tests"
    ref = definition("a01")["reference"]
    # Replay is deliberately mocked locally. Actual alternative/hostile SQL runs on Actions.
    gold = json.loads((task / "gold.json").read_text())
    originals = {a["sql"]: a["value"] for a in ref["answers"]}
    identifiers = {a["sql"]: a["id"] for a in ref["answers"]}
    def replay(sql, db):
        if db.name == "data.sqlite":
            return originals[sql]
        control = next(c for c in gold["controls"] if c["database"] == db.name)
        return control["expected"][identifiers[sql]]
    monkeypatch.setattr(scorer, "replay", replay)
    ref["answers"][0]["value"] = 0.14
    (tmp_path / "answer.json").write_text(json.dumps(ref))
    verdict = scorer.grade(tmp_path, task)
    assert verdict["checks"]["delivery"] is True
    assert verdict["checks"]["financial_answer"] is False
    assert verdict["checks"]["evidence"] is True
    assert verdict["verified_research_completion"] is False


def test_equivalent_evidence_and_shared_context():
    paths = [["facts", "definition"], ["combined"]]
    assert scorer.support(["facts", "definition"], paths, ["definition"])
    assert scorer.support(["combined", "definition"], paths, ["definition"])
    assert not scorer.support(["facts", "unrelated"], paths, ["definition"])
    assert not scorer.support(["facts"], paths, ["definition"])
