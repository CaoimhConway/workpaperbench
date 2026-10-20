import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
SPEC = importlib.util.spec_from_file_location('workflow_regression', ROOT / 'scripts/workflow_regression.py')
REGRESSION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REGRESSION)
NATIVE = REGRESSION.native


def trial(directory, key='c01', reward=1.0):
    task = ROOT / NATIVE.TASKS / key
    reference = json.loads((task / 'tests/reference.json').read_text())
    gold = json.loads((task / 'tests/gold.json').read_text())
    positive = reward == 1
    directory.mkdir(parents=True)
    result = {'task_name': 'workpaperbench/' + reference['task_id'],
        'exception_info': None, 'verifier_environment_mode': 'separate',
        'verifier_result': {'rewards': {'reward': reward}},
        'config': {'task': {'path': str(task), 'git_url': None}}}
    verdict = {'scorer_version': gold['scorer_version'], 'complete': positive,
        'checks': {name: True if positive else None for name in NATIVE.DIMENSIONS},
        'isolation': {name: True for name in NATIVE.ISOLATION},
        'errors': [] if positive else ['delivery:ValidationError'],
        'details': {'tables': {}, 'claims': {}}}
    verdict['checks']['delivery'] = positive
    if positive:
        verdict['details']['tables'] = {row['id']: {'original': True, 'evidence': True,
            'controls': {control['name']: True for control in gold['controls']}}
            for row in reference['tables']}
        verdict['details']['claims'] = {row['id']: {'verdict': True, 'evidence': True}
                                        for row in reference['claims']}
    (directory / 'result.json').write_text(json.dumps(result))
    (directory / 'verifier').mkdir()
    (directory / 'verifier/verdict.json').write_text(json.dumps(verdict))
    delivery = directory / 'artifacts/logs/artifacts'
    delivery.mkdir(parents=True)
    (delivery / 'answer.json').write_text(json.dumps(reference if positive else {}))
    if positive:
        for row in reference['tables']:
            shutil.copyfile(task / 'solution' / row['file'], delivery / row['file'])
    return directory / 'result.json', task


def test_checkout_is_explicit_and_default_remains_pinned_release():
    assert NATIVE.task_arguments() == ['--repo', NATIVE.REPO, '-p', NATIVE.TASKS]
    assert NATIVE.task_arguments(True) == ['-p', str(ROOT / NATIVE.TASKS)]


def test_controller_credentials_do_not_enter_regression_children(monkeypatch):
    for name in ('GH_TOKEN', 'GITHUB_TOKEN', 'OPENAI_API_KEY', 'WPB_MODEL_API_KEY'):
        monkeypatch.setenv(name, 'private-fixture-value')
    environment = NATIVE.child_environment()
    assert not any(name in environment for name in ('GH_TOKEN', 'GITHUB_TOKEN', 'OPENAI_API_KEY', 'WPB_MODEL_API_KEY'))


@pytest.mark.parametrize('reward', [1.0, 0.0])
def test_native_positive_and_delivery_rejection_bind_exact_artifacts(tmp_path, reward):
    path, task = trial(tmp_path / 'trial', reward=reward)
    result = NATIVE.check_trial(path, task, reward, checkout=True)
    assert result['reward'] == reward
    assert len(result['retained_sql_sha256']) == (3 if reward else 0)
    assert all(result['isolation'].values())


@pytest.mark.parametrize('change', ['wrong-reward', 'native-exception', 'public-release-source',
                                  'different-checkout', 'missing-isolation', 'nonboolean-check', 'missing-table', 'missing-control'])
def test_wrong_rewards_missing_diagnostics_and_foreign_sources_fail(tmp_path, change):
    path, task = trial(tmp_path / 'trial')
    result = json.loads(path.read_text())
    verdict_path = path.parent / 'verifier/verdict.json'
    verdict = json.loads(verdict_path.read_text())
    if change == 'wrong-reward':
        result['verifier_result']['rewards']['reward'] = 0.0
    elif change == 'native-exception':
        result['exception_info'] = {'exception_type': 'FixtureFailure'}
    elif change == 'public-release-source':
        result['config']['task']['git_url'] = 'https://github.com/CaoimhConway/workpaperbench.git'
    elif change == 'different-checkout':
        result['config']['task']['path'] = str(task.parent / 'c02')
    elif change == 'missing-isolation':
        verdict['isolation'].pop('no_inference_key')
    elif change == 'nonboolean-check':
        verdict['checks']['evidence'] = 1
    elif change == 'missing-table':
        verdict['details']['tables'].pop(next(iter(verdict['details']['tables'])))
    elif change == 'missing-control':
        controls = next(iter(verdict['details']['tables'].values()))['controls']
        controls.pop(next(iter(controls)))
    path.write_text(json.dumps(result))
    verdict_path.write_text(json.dumps(verdict))
    with pytest.raises(ValueError):
        NATIVE.check_trial(path, task, 1.0, checkout=True)


def test_passing_diagnostics_cannot_hide_changed_delivered_sql(tmp_path):
    path, task = trial(tmp_path / 'trial')
    sql = next((path.parent / 'artifacts/logs/artifacts').glob('*.sql'))
    sql.write_text('SELECT 0')
    with pytest.raises(ValueError, match='unexpected_retained_sql'):
        NATIVE.check_trial(path, task, 1.0, checkout=True)


@pytest.mark.parametrize('failure', [None, 'oracle', 'job-diagnostics'])
def test_regression_retains_failures_and_uses_current_checkout(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(REGRESSION.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(REGRESSION.subprocess, 'check_output', lambda *args, **kwargs: '0.23.0\n')
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        assert '--repo' not in command
        assert command[command.index('-p') + 1] == str(ROOT / NATIVE.TASKS)
        jobs = Path(command[command.index('--jobs-dir') + 1]) / 'oracles'
        for key in REGRESSION.TASKS:
            trial(jobs / (key + '__fixture'), key)
        job = {'n_total_trials': 4, 'stats': {'n_completed_trials': 4, 'n_errored_trials': 0,
            'n_running_trials': 0, 'n_pending_trials': 0, 'n_cancelled_trials': 0, 'n_retries': 0}}
        if failure == 'job-diagnostics':
            job['stats'].pop('n_retries')
        if failure == 'oracle':
            path = jobs / 'b01__fixture/result.json'
            data = json.loads(path.read_text())
            data['verifier_result']['rewards']['reward'] = 0.0
            path.write_text(json.dumps(data))
        (jobs / 'result.json').write_text(json.dumps(job))
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr(REGRESSION.subprocess, 'run', run)
    fixtures = []
    def validate(binary, output, checkout):
        assert checkout is True
        fixtures.append(output)
        return {'inference': False, 'cases': [{'reward': 1.0}, {'reward': 0.0}]}
    monkeypatch.setattr(NATIVE, 'validate', validate)
    output = tmp_path / 'regression.json'
    if failure:
        with pytest.raises(ValueError):
            REGRESSION.run('harbor', output)
        report = json.loads(output.read_text())
        assert report['status'] == 'failed' and report['error']
        assert not fixtures
    else:
        report = REGRESSION.run('harbor', output)
        assert report['status'] == 'passed' and len(report['oracles']) == 4
        assert report['source']['kind'] == 'checkout' and fixtures
        assert report['inference'] is False and report['model_performance_evaluation'] is False
    assert len(calls) == 1
