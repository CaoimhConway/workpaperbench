import copy
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location(
    'workpaperbench.workflow_scoring_revision', ROOT / 'config/scorers/workflow-1.2.0.py')
SCORER = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(SCORER)


def table():
    return {
        'columns': {
            'category': {'type': 'text', 'aliases': {'Bitcoin revenue': 'Bitcoin',
                                                   'Hardware revenue': 'Hardware'}},
            'contribution_pct': {'type': 'real', 'tolerance': 1e-6},
        },
        'keys': ['category'],
        'rows': [['Bitcoin', 31.780786510832355], ['Hardware', -0.917100066674073]],
    }


def test_declared_aliases_keep_semantic_rows_and_column_permutations():
    spec = table()
    actual = {'columns': ['contribution_pct', 'category'],
              'rows': [[spec['rows'][1][1], 'Hardware revenue'],
                       [spec['rows'][0][1], 'Bitcoin revenue']]}
    assert SCORER.compare(actual, spec, spec['rows'])
    assert actual['rows'][0][1] == 'Hardware revenue'
    actual['rows'][0][0], actual['rows'][1][0] = actual['rows'][1][0], actual['rows'][0][0]
    assert not SCORER.compare(actual, spec, spec['rows'])


@pytest.mark.parametrize('label', ['bitcoin revenue', 'Bitcoin revenues', 'Unrelated'])
def test_undeclared_labels_are_not_fuzzily_matched(label):
    spec = table()
    actual = {'columns': list(spec['columns']), 'rows': copy.deepcopy(spec['rows'])}
    actual['rows'][0][0] = label
    assert not SCORER.compare(actual, spec, spec['rows'])


def test_normalized_duplicate_keys_are_rejected_even_with_equal_numbers():
    spec = table()
    spec['rows'][1][1] = spec['rows'][0][1]
    actual = {'columns': list(spec['columns']),
              'rows': [['Bitcoin', spec['rows'][0][1]], ['Bitcoin revenue', spec['rows'][1][1]]]}
    assert not SCORER.compare(actual, spec, spec['rows'])


@pytest.mark.parametrize('wrong', [0.31780786510832355, 31.78079, '31.780786510832355', True, None])
def test_aliases_preserve_numeric_units_tolerances_and_types(wrong):
    spec = table()
    actual = {'columns': list(spec['columns']), 'rows': copy.deepcopy(spec['rows'])}
    actual['rows'][0] = ['Bitcoin revenue', wrong]
    assert not SCORER.compare(actual, spec, spec['rows'])


def test_percentage_point_to_basis_point_error_remains_a_failure():
    expected = 10000 * (31653 / 69632 - 30552 / 65585)
    spec = {'columns': {'fiscal_year': {'type': 'integer'},
                        'margin_qoq_bps': {'type': 'real', 'tolerance': 1e-6}},
            'keys': ['fiscal_year']}
    actual = {'columns': list(spec['columns']), 'rows': [[2025, expected]]}
    assert SCORER.compare(actual, spec, [[2025, expected]])
    actual['rows'][0][1] = expected * 100
    assert not SCORER.compare(actual, spec, [[2025, expected]])


@pytest.mark.parametrize('actual, reason', [
    (None, 'sql_execution'),
    ({'columns': ['category', 'wrong_unit'], 'rows': []}, 'columns'),
    ({'columns': ['category', 'contribution_pct'], 'rows': []}, 'rows'),
    ({'columns': ['category', 'contribution_pct'], 'rows': [['Unknown', 31], ['Hardware', -1]]}, 'keys'),
    ({'columns': ['category', 'contribution_pct'], 'rows': [['Bitcoin', 0.3178], ['Hardware', -1]]}, 'numeric'),
])
def test_diagnostics_separate_execution_contract_and_numeric_errors(actual, reason):
    spec = table()
    assert SCORER.comparison_error(actual, spec, spec['rows']) == reason


@pytest.mark.parametrize('evidence', [
    ['a03:s02', 'a03:s03'],
    ['(a03:s02), [a03:s03].'],
    ['a03:s03 and a03:s02 - report and six-month totals', 'Definition: subtract Q2 from the half-year'],
    ['a03:s02 - current quarter', 'a03:s02 - prior quarter', 'a03:s03 - both six-month totals'],
    ['a03:s02/a03:s03', 'Derived values are calculated in quarter_model.sql'],
    ['a03:s02 and a03:s03 - FY2025:Q2 values', 'Definition:margin is operating income divided by revenue'],
])
def test_source_ids_in_explanatory_citations_are_accepted(evidence):
    assert SCORER.supported(evidence, [['a03:s02', 'a03:s03']], [])


@pytest.mark.parametrize('extra', ['a03:s99', 'b01:s01', 'invented:s01',
                                  'a03:s02suffix', 'prefix-a03:s02',
                                  '9a03:s02', 'a03:S02'])
def test_every_unknown_or_unrelated_citation_is_rejected(extra):
    assert not SCORER.supported(['a03:s02 and a03:s03, also ' + extra],
                                [['a03:s02', 'a03:s03']], [])


def test_prose_does_not_replace_evidence_or_allow_source_dumping():
    options = [['a03:s02', 'a03:s03'], ['a03:s01']]
    assert SCORER.supported(['a03:s01 with a03:s04 context'], options, ['a03:s04'])
    assert not SCORER.supported(['The filing supports this answer'], options, ['a03:s04'])
    assert not SCORER.supported(['FY2025:Q2, Definition:margin'], options, ['a03:s04'])
    assert not SCORER.supported(['a03:s02'], options, ['a03:s04'])
    assert not SCORER.supported(['a03:s01 a03:s02 a03:s03 a03:s04 a03:s05'], options, ['a03:s04'])


def artifacts(tmp_path, monkeypatch):
    task = ROOT / 'datasets/workflow-v5/tasks/a01'
    trusted = tmp_path / 'trusted'
    shutil.copytree(task / 'tests', trusted)
    gold = json.loads((trusted / 'gold.json').read_text())
    answer = json.loads((trusted / 'reference.json').read_text())
    directory = tmp_path / 'submission'
    directory.mkdir()
    (directory / 'answer.json').write_text(json.dumps(answer))
    for entry in answer['tables']:
        (directory / entry['file']).write_text(entry['id'])

    def authored_result(identifier, database):
        spec = gold['tables'][identifier]
        rows = spec['rows'] if database.name == 'data.sqlite' else next(
            control['tables'][identifier] for control in gold['controls']
            if control['database'] == database.name)
        return {'columns': list(spec['columns']), 'rows': copy.deepcopy(rows)}

    monkeypatch.setattr(SCORER, 'replay', authored_result)
    return directory, trusted, answer, gold


def test_numerical_and_claim_diagnostics_are_independent(tmp_path, monkeypatch):
    directory, trusted, answer, gold = artifacts(tmp_path, monkeypatch)
    answer['claims'][0]['verdict'] = 'unresolved'
    (directory / 'answer.json').write_text(json.dumps(answer))
    verdict = SCORER.grade(directory, trusted)
    assert verdict['checks'] == dict(financial_answer=False, numerical_tables=True,
                                    claim_verdicts=False, evidence=True,
                                    robustness=True, delivery=True)
    answer['claims'][0]['verdict'] = gold['claims'][answer['claims'][0]['id']]['verdict']
    (directory / 'answer.json').write_text(json.dumps(answer))
    authored = SCORER.replay

    def wrong_basis_points(identifier, database):
        result = authored(identifier, database)
        if identifier == 'quarter_reconciliation':
            result['rows'][0][-1] *= 100
        return result

    monkeypatch.setattr(SCORER, 'replay', wrong_basis_points)
    verdict = SCORER.grade(directory, trusted)
    assert verdict['checks'] == dict(financial_answer=False, numerical_tables=False,
                                    claim_verdicts=True, evidence=True,
                                    robustness=False, delivery=True)
    table_result = verdict['details']['tables']['quarter_reconciliation']
    assert table_result['original_error'] == 'numeric'
    assert set(table_result['control_errors'].values()) == {'numeric'}


def test_ambiguous_legacy_verdicts_require_explicit_gold_permission(tmp_path, monkeypatch):
    directory, trusted, answer, gold = artifacts(tmp_path, monkeypatch)
    claim = answer['claims'][-1]
    assert gold['claims'][claim['id']]['verdict'] == 'unresolved'
    claim['verdict'] = 'contradicted'
    claim['note'] = 'Optional prose is not semantically graded.'
    (directory / 'answer.json').write_text(json.dumps(answer))
    assert SCORER.grade(directory, trusted)['checks']['claim_verdicts'] is False
    gold['claims'][claim['id']]['accepted_verdicts'] = ['unresolved', 'contradicted']
    (trusted / 'gold.json').write_text(json.dumps(gold))
    assert SCORER.grade(directory, trusted)['complete'] is True
    claim['verdict'] = 'supported'
    (directory / 'answer.json').write_text(json.dumps(answer))
    assert SCORER.grade(directory, trusted)['checks']['claim_verdicts'] is False


def test_rejected_delivery_leaves_all_semantic_aggregates_unassessed(tmp_path, monkeypatch):
    directory, trusted, answer, _ = artifacts(tmp_path, monkeypatch)
    (directory / answer['tables'][0]['file']).unlink()
    monkeypatch.setattr(SCORER, 'replay', lambda *_: pytest.fail('Rejected SQL reached replay'))
    verdict = SCORER.grade(directory, trusted)
    assert verdict['checks'] == dict(financial_answer=None, numerical_tables=None,
                                    claim_verdicts=None, evidence=None,
                                    robustness=None, delivery=False)
    assert all(claim['partial_only'] for claim in verdict['details']['claims'].values())
