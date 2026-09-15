"""Reviewed financial evidence paths and structural gating for new workpapers."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'workpaperbench.challenge_evidence_scorer', ROOT / 'config/scorers/challenge-1.1.0.py'
)
SCORER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SCORER
SPEC.loader.exec_module(SCORER)


def score(tmp_path, monkeypatch, key, answer):
    trusted = ROOT / 'datasets/challenge-v1/tasks' / key / 'tests'
    ref = json.loads((trusted / 'reference.json').read_text())
    gold = json.loads((trusted / 'gold.json').read_text())
    by_sql = {a['sql']: a for a in ref['answers'] if a['sql']}

    def replay(sql, database):
        claim = by_sql[sql]
        if database.name == 'data.sqlite':
            return claim['value']
        control = next(c for c in gold['controls'] if c['database'] == database.name)
        return control['expected'][claim['id']]

    monkeypatch.setattr(SCORER, 'replay', replay)
    (tmp_path / 'answer.json').write_text(json.dumps(answer))
    return SCORER.grade(tmp_path, trusted)


@pytest.mark.parametrize('key', ['c02', 'c03', 'c04'])
def test_minimal_facts_and_optional_shared_definitions(tmp_path, monkeypatch, key):
    trusted = ROOT / 'datasets/challenge-v1/tasks' / key / 'tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    verdict = score(tmp_path, monkeypatch, key, answer)
    assert verdict['verified_research_completion'] is True
    gold = json.loads((trusted / 'gold.json').read_text())
    answer['context_evidence'] = gold['context_evidence_allowed']
    for claim in answer['answers']:
        claim['evidence'] = [s for s in claim['evidence'] if s not in answer['context_evidence']]
    answer['conclusion']['evidence'] = [s for s in answer['conclusion']['evidence']
                                       if s not in answer['context_evidence']]
    assert score(tmp_path, monkeypatch, key, answer)['verified_research_completion'] is True


def test_unrelated_cash_app_population_does_not_support_consolidated_claim(tmp_path, monkeypatch):
    trusted = ROOT / 'datasets/challenge-v1/tasks/c03/tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    claim = next(a for a in answer['answers']
                 if a['id'] == 'bitcoin_share_of_total_net_revenue_increase_pct')
    claim['evidence'].append('c03:s04')
    verdict = score(tmp_path, monkeypatch, 'c03', answer)
    assert verdict['checks']['evidence'] is False
    assert verdict['checks']['financial_answer'] is True


def test_duplicate_claim_within_new_schema_bound_executes_no_sql(tmp_path, monkeypatch):
    trusted = ROOT / 'datasets/challenge-v1/tasks/a02/tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    assert len(answer['answers']) == 4
    answer['answers'].append(copy.deepcopy(answer['answers'][0]))
    assert len(answer['answers']) == 5
    answer['answers'][0]['sql'] = 'DELETE FROM financials'
    (tmp_path / 'answer.json').write_text(json.dumps(answer))
    monkeypatch.setattr(SCORER, 'replay', lambda *args: pytest.fail('SQL on duplicate claim'))
    verdict = SCORER.grade(tmp_path, trusted)
    assert verdict['checks']['delivery'] is False
    assert verdict['checks']['robustness'] is None
