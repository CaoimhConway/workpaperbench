"""A valid score must distinguish repairs from damage and missing observations."""
import copy

import pytest

from workpaperbench.workflow_report import change, summarize


def table(original=True, duplicate=True):
    return {'original': original, 'controls': {'duplicate': duplicate}}


def inputs():
    identity = dict(manifest_id='catalog', task_id='workflow-v7-b01',
                    task_sha256='task', scorer_sha256='scorer')
    baseline = {**identity, 'tables': {'coverage': table(False, False), 'bridge': table()}}
    row = {**identity, 'attempt_id': 'attempt', 'status': 'verified', 'inference': True,
        'verdict': {'checks': dict(numerical_tables=True, claim_verdicts=True,
                                 evidence=True, robustness=False, delivery=True),
                    'details': {'tables': {'coverage': table(True, False), 'bridge': table(False)}}}}
    return row, baseline


def test_original_repair_does_not_hide_control_defect_or_regression():
    row, baseline = inputs()
    result = summarize(row, [baseline])
    assert result['tables']['coverage']['original_inputs'] == 'Repair'
    assert result['tables']['coverage']['original_and_controls'] == 'Unrepaired'
    assert result['tables']['bridge']['original_and_controls'] == 'Regression'
    assert result['opportunities']['original_and_controls'] == {
        'initially_incorrect': 1, 'initially_correct': 1}
    assert result['tables']['coverage']['failed_controls'] == {'duplicate': 'mismatch'}


@pytest.mark.parametrize('before,after,expected', [
    (True, True, 'Preservation'), (True, False, 'Regression'),
    (False, True, 'Repair'), (False, False, 'Unrepaired')])
def test_transitions(before, after, expected):
    assert change(table(before), table(after))['original_and_controls'] == expected


@pytest.mark.parametrize('status', ['infrastructure_failed', 'cancelled', 'started'])
def test_infrastructure_is_not_bad_financial_reasoning(status):
    row, baseline = inputs()
    row['status'] = status
    result = summarize(row, [baseline])
    assert result['transition_counts']['original_and_controls'] == {'Unassessed': 2}
    assert result['failure_dimensions'] == dict(reasoning_or_calculation='unassessed',
        evidence='unassessed', robustness='unassessed', delivery='unassessed', infrastructure='fail')


def test_missing_delivery_does_not_count_as_unrepaired_sql():
    row, baseline = inputs()
    row['status'] = 'candidate_failed'
    row['candidate_error_type'] = 'AgentTimeoutError'
    row['verdict'] = {'checks': {'delivery': False}}
    result = summarize(row, [baseline])
    assert result['transition_counts']['original_inputs'] == {'Unassessed': 2}
    assert result['failure_dimensions']['delivery'] == 'fail'
    assert result['failure_dimensions']['reasoning_or_calculation'] == 'unassessed'
    assert result['failure_dimensions']['infrastructure'] == 'pass'


@pytest.mark.parametrize('field', ['task_sha256', 'scorer_sha256', 'manifest_id'])
def test_changed_identity_cannot_borrow_baseline(field):
    row, baseline = inputs()
    baseline[field] = 'different'
    result = summarize(row, [baseline])
    assert result['baseline_matched'] is False
    assert result['opportunities'] is None
    assert result['transition_counts']['original_inputs'] == {'Unassessed': 2}


def test_incomparable_controls_and_partial_tables_are_rejected():
    row, baseline = inputs()
    changed = copy.deepcopy(row)
    changed['verdict']['details']['tables']['coverage']['controls'] = {'scale': True}
    with pytest.raises(ValueError, match='control_sets_differ'):
        summarize(changed, [baseline])
    del row['verdict']['details']['tables']['coverage']
    with pytest.raises(ValueError, match='table_sets_differ'):
        summarize(row, [baseline])


def test_retained_submissions_reproduce_control_inclusive_transitions():
    import hashlib
    import json
    from collections import Counter
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    baseline = json.loads((root / 'reports/workflow-v7/starting-sql.json').read_text())
    replay = json.loads((root / 'reports/workflow-v5/corrected-replay.json').read_text())
    counts = Counter()
    for item in replay['attempts']:
        directory = root / 'reports/workflow-v5/submissions' / item['attempt_id']
        original = json.loads((directory / 'receipt.json').read_text())
        assert summarize(original, baseline['baselines'])['failure_dimensions']['reasoning_or_calculation'] == 'fail'
        for name, expected in item['files_sha256'].items():
            assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == expected
        row = {**item, 'manifest_id': replay['base_manifest_id'],
            'scorer_sha256': replay['scorer_sha256'], 'task_id': 'workflow-v5-' + item['task'],
            'task_sha256': item['reviewed_task_sha256'], 'status': 'verified'}
        result = summarize(row, baseline['baselines'])
        assert result['baseline_matched']
        counts.update(result['transition_counts']['original_and_controls'])
    assert counts == dict(Repair=2, Preservation=5, Regression=1, Unrepaired=1)
