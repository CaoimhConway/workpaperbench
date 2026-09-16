"""Unavailable payment counts must not pass as guessed numeric answers."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_challenge_tasks as builder

SCORER_PATH = ROOT / "config/scorers/challenge-1.1.0.py"
spec = importlib.util.spec_from_file_location(
    "workpaperbench.challenge_grading_110_payment_count", SCORER_PATH
)
scorer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scorer
spec.loader.exec_module(scorer)


def test_invented_business_payment_count_fails_financial_gate_without_sql(tmp_path, monkeypatch):
    definition = json.loads(
        (ROOT / "datasets/challenge-v1/authoring/c02/definition.json").read_text()
    )
    package = tmp_path / "package"
    builder.package(definition, package)
    trusted = package / "tasks/c02/tests"
    gold = json.loads((trusted / "gold.json").read_text())
    answer = copy.deepcopy(definition["reference"])
    invented = next(
        claim for claim in answer["answers"]
        if claim["id"] == "business_payment_count_2024"
    )
    invented.update(
        status="answered",
        value=1,
        unit="count",
        reason_code=None,
        evidence=["c02:s03", "c02:s04"],
        sql="SELECT 1",
    )
    answer_dir = tmp_path / "answer"
    answer_dir.mkdir()
    (answer_dir / "answer.json").write_text(json.dumps(answer))

    positive_by_sql = {
        claim["sql"]: claim["id"]
        for claim in definition["reference"]["answers"]
        if claim["status"] == "answered"
    }
    positive_values = {
        claim["id"]: claim["value"]
        for claim in definition["reference"]["answers"]
        if claim["status"] == "answered"
    }
    replay_calls = []

    def mocked_replay(sql, database):
        replay_calls.append((sql, database.name))
        assert sql in positive_by_sql
        identifier = positive_by_sql[sql]
        if database.name == "data.sqlite":
            return positive_values[identifier]
        control = next(
            item for item in gold["controls"]
            if item["database"] == database.name
        )
        return control["expected"][identifier]

    monkeypatch.setattr(scorer, "replay", mocked_replay)
    verdict = scorer.grade(answer_dir, trusted)

    assert verdict["checks"]["delivery"] is True
    assert verdict["checks"]["evidence"] is True
    assert verdict["checks"]["robustness"] is True
    assert verdict["checks"]["financial_answer"] is False
    assert verdict["verified_research_completion"] is False
    count_detail = verdict["details"]["claims"]["business_payment_count_2024"]
    assert count_detail["availability"] is False
    assert count_detail["unit"] is True
    assert count_detail["evidence"] is True
    assert len(replay_calls) == len(positive_by_sql) * (1 + len(gold["controls"]))
    assert all(sql != invented["sql"] for sql, _ in replay_calls)
