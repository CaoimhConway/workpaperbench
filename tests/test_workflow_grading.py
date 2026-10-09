import copy
import json
from pathlib import Path

import pytest

from workpaperbench import workflow_grading as grading
from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]


def block_spec():
    _, _, path = load(ROOT, 'workflow-v1', 'c01')
    return json.loads((path / 'tests/gold.json').read_text())['tables']['revenue_bridge']


def test_result_comparison_accepts_row_and_column_permutations():
    spec = block_spec()
    columns = list(reversed(spec['columns']))
    original = list(spec['columns'])
    result = {'columns': columns, 'rows': [[row[original.index(name)] for name in columns] for row in reversed(spec['rows'])]}
    assert grading.compare(result, spec, spec['rows'])


def test_equal_values_do_not_collapse_different_category_keys():
    spec = block_spec()
    rows = copy.deepcopy(spec['rows'])
    rows[1][1:] = rows[0][1:]
    assert grading.compare({'columns': list(spec['columns']), 'rows': rows}, spec, rows)
    duplicate = copy.deepcopy(rows)
    duplicate[1][0] = duplicate[0][0]
    assert not grading.compare({'columns': list(spec['columns']), 'rows': duplicate}, spec, rows)


@pytest.mark.parametrize('wrong', [None, True, float('nan'), float('inf'), '31.78'])
def test_numeric_table_cells_reject_nonfinite_or_wrong_types(wrong):
    spec = block_spec()
    result = {'columns': list(spec['columns']), 'rows': copy.deepcopy(spec['rows'])}
    result['rows'][0][4] = wrong
    assert not grading.compare(result, spec, spec['rows'])


def test_share_change_cannot_replace_growth_contribution():
    spec = block_spec()
    result = {'columns': list(spec['columns']), 'rows': copy.deepcopy(spec['rows'])}
    for row in result['rows']:
        row[4] = row[7]
    assert not grading.compare(result, spec, spec['rows'])


def test_structurally_rejected_artifacts_never_execute_sql(tmp_path, monkeypatch):
    _, _, path = load(ROOT, 'workflow-v1', 'a01')
    answer = json.loads((path / 'tests/reference.json').read_text())
    answer['tables'][0]['file'] = '../escape.sql'
    (tmp_path / 'answer.json').write_text(json.dumps(answer))
    def forbidden(*arguments):
        raise AssertionError('replay executed after structural rejection')
    monkeypatch.setattr(grading, 'replay', forbidden)
    verdict = grading.grade(tmp_path, path / 'tests')
    assert verdict['checks']['delivery'] is False
    assert verdict['checks']['financial_answer'] is None
    assert verdict['checks']['robustness'] is None
    assert all(item['verdict'] and item['partial_only'] for item in verdict['details']['claims'].values())
    assert len(verdict['details']['claims']) == 3


def test_sql_symlinks_are_rejected_before_replay(tmp_path, monkeypatch):
    _, _, path = load(ROOT, 'workflow-v1', 'a01')
    answer = json.loads((path / 'tests/reference.json').read_text())
    (tmp_path / 'answer.json').write_text(json.dumps(answer))
    for item in answer['tables']:
        (tmp_path / item['file']).symlink_to(path / 'solution' / item['file'])
    monkeypatch.setattr(grading, 'replay', lambda *_: pytest.fail('unsafe SQL executed'))
    assert grading.grade(tmp_path, path / 'tests')['checks']['delivery'] is False


def test_prototypes_keep_authentic_and_synthetic_provenance_separate():
    manifest = load(ROOT, 'workflow-v1')
    assert len(manifest['tasks']) == 3
    for key in manifest['tasks']:
        _, _, path = load(ROOT, 'workflow-v1', key)
        authoring = json.loads((path / 'authoring.json').read_text())
        assert authoring['split'] == 'development'
        assert 'never held out' in authoring['exposure']
        assert authoring['human_review'] == 'pending'
        gold = json.loads((path / 'tests/gold.json').read_text())
        assert 2 <= len(gold['controls']) <= 4
        assert all(control['origin'] == 'authored_synthetic_counterfactual' for control in gold['controls'])


def test_duplicate_claims_are_not_chosen_for_partial_diagnostics(tmp_path, monkeypatch):
    _, _, path = load(ROOT, 'workflow-v1', 'a01')
    answer = json.loads((path / 'tests/reference.json').read_text())
    answer['claims'].append(copy.deepcopy(answer['claims'][0]))
    answer['claims'][-1]['verdict'] = 'contradicted'
    (tmp_path / 'answer.json').write_text(json.dumps(answer))
    monkeypatch.setattr(grading, 'replay', lambda *_: pytest.fail('rejected SQL executed'))
    verdict = grading.grade(tmp_path, path / 'tests')
    assert answer['claims'][0]['id'] not in verdict['details']['claims']
    assert len(verdict['details']['claims']) == 2
