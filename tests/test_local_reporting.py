import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location('local_bench', Path(__file__).parents[1] / 'scripts/local_bench.py')
LOCAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOCAL)


def receipt(root, name, configuration='profile-1'):
    directory = root / '.raw/local-trials' / name
    (directory / 'raw-sql').mkdir(parents=True)
    (directory / 'raw-sql/result.sql').write_text('SELECT 1 value')
    (directory / 'verifier.json').write_text('{}')
    record = {'attempt_id': name, 'manifest_id': 'manifest-1', 'scorer_sha256': 'scorer-1',
              'inference': True, 'model_configuration_sha256': configuration,
              'verdict_sha256': hashlib.sha256(b'{}').hexdigest(),
              'sql_file_sha256': {'result.sql': hashlib.sha256(b'SELECT 1 value').hexdigest()}}
    (directory / 'receipt.json').write_text(json.dumps(record))
    return directory


def test_report_rejects_changed_retained_sql(tmp_path, monkeypatch):
    directory = receipt(tmp_path, 'attempt-1')
    (directory / 'raw-sql/result.sql').write_text('SELECT 2 value')
    monkeypatch.setattr(LOCAL, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='retained_sql_changed'):
        LOCAL.report(['attempt-1'], tmp_path / 'report.json')
    assert not (tmp_path / 'report.json').exists()


def test_report_rejects_mixed_model_configurations(tmp_path, monkeypatch):
    receipt(tmp_path, 'attempt-1')
    receipt(tmp_path, 'attempt-2', 'changed-context')
    monkeypatch.setattr(LOCAL, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='configurations_differ'):
        LOCAL.report(['attempt-1', 'attempt-2'], tmp_path / 'report.json')


def test_report_rejects_repeated_attempt_ids(tmp_path, monkeypatch):
    receipt(tmp_path, 'attempt-1')
    monkeypatch.setattr(LOCAL, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='distinct_attempts'):
        LOCAL.report(['attempt-1', 'attempt-1'], tmp_path / 'report.json')


def test_report_rejects_mixed_input_tracks(tmp_path, monkeypatch):
    receipt(tmp_path, 'attempt-1')
    directory = receipt(tmp_path, 'attempt-2')
    path = directory / 'receipt.json'
    data = json.loads(path.read_text())
    data['evaluation_track'] = 'construction'
    path.write_text(json.dumps(data))
    monkeypatch.setattr(LOCAL, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='evaluation_tracks_differ'):
        LOCAL.report(['attempt-1', 'attempt-2'], tmp_path / 'report.json')


def test_report_does_not_replace_prior_output(tmp_path, monkeypatch):
    receipt(tmp_path, 'attempt-1')
    monkeypatch.setattr(LOCAL, 'ROOT', tmp_path)
    output = tmp_path / 'report.json'
    LOCAL.report(['attempt-1'], output)
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        LOCAL.report(['attempt-1'], output)
    assert output.read_bytes() == original


def test_report_rejects_rebound_attempt_identity(tmp_path, monkeypatch):
    directory = receipt(tmp_path, 'attempt-1')
    path = directory / 'receipt.json'
    data = json.loads(path.read_text())
    data['attempt_id'] = 'different-attempt'
    path.write_text(json.dumps(data))
    monkeypatch.setattr(LOCAL, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='attempt_identity_changed'):
        LOCAL.report(['attempt-1'], tmp_path / 'report.json')


def test_report_rejects_changed_embedded_verdict(tmp_path, monkeypatch):
    directory = receipt(tmp_path, 'attempt-1')
    path = directory / 'receipt.json'
    record = json.loads(path.read_text())
    record['verdict'] = {'complete': True}
    path.write_text(json.dumps(record))
    monkeypatch.setattr(LOCAL, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='verdict_receipt_mismatch'):
        LOCAL.report(['attempt-1'], tmp_path / 'report.json')
    assert not (tmp_path / 'report.json').exists()


def test_separate_attempts_exclude_prior_idle_server_observations(tmp_path):
    path = tmp_path / 'settings.jsonl'
    first = {'id_task': 98, 'params': {'seed': 17}}
    second = {'id_task': 283, 'params': {'seed': 17}}
    path.write_text(json.dumps(first) + '\n')
    start = len(LOCAL.server_observations(path))
    # The actual server's idle slot omits id_task, so its value cannot mark a trial.
    with path.open('a') as output:
        output.write(json.dumps(second) + '\n')
    assert LOCAL.server_observations(path, start) == [second]
    assert LOCAL.server_observations(path) == [first, second]

@pytest.mark.parametrize('candidate_error', ['NonZeroAgentExitCodeError', 'AgentTimeoutError'])
def test_queue_finishes_after_candidate_failure_and_restart_skips_slots(tmp_path, monkeypatch, candidate_error):
    from types import SimpleNamespace
    (tmp_path / '.local').mkdir()
    (tmp_path / 'profile.json').write_text('{}')
    profile_hash = hashlib.sha256(b'{}').hexdigest()
    schedule = {
        'schedule_id': 'fixture-queue', 'model_configuration': 'profile.json',
        'model_configuration_sha256': profile_hash, 'execution_files_sha256': {},
        'manifest_id': 'manifest-1', 'scorer_sha256': 'scorer-1', 'report': 'report.json',
        'attempts': [{'attempt_id': name, 'task_id': 'workflow-v5-' + name, 'task_sha256': name}
                     for name in ('first', 'second')]}
    path = tmp_path / 'schedule.json'
    path.write_text(json.dumps(schedule))
    monkeypatch.setattr(LOCAL, 'ROOT', tmp_path)
    monkeypatch.setattr(LOCAL, 'load', lambda root, dataset, task: (
        {'manifest_id': 'manifest-1', 'scorer_sha256': 'scorer-1'},
        {'split': 'development', 'task_sha256': task}, None))
    invoked = []

    def run(command, **kwargs):
        name = command[command.index('--attempt') + 1]
        invoked.append(name)
        directory = receipt(tmp_path, name, profile_hash)
        record = json.loads((directory / 'receipt.json').read_text())
        record.update(task_id='workflow-v5-' + name, task_sha256=name, status='candidate_failed' if name == 'first' else 'verified')
        if name == 'first':
            record['candidate_error_type'] = candidate_error
        (directory / 'receipt.json').write_text(json.dumps(record))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(LOCAL.subprocess, 'run', run)
    LOCAL.run_queue(path)
    LOCAL.run_queue(path)
    assert invoked == ['first', 'second']
    result = json.loads((tmp_path / 'report.json').read_text())
    assert [row['status'] for row in result['attempts']] == ['candidate_failed', 'verified']
    status = json.loads((tmp_path / '.local/fixture-queue-status.json').read_text())
    assert status['status'] == 'completed'
    assert len(status['outcomes']) == 2
    (tmp_path / '.raw/local-trials/first/raw-sql/result.sql').write_text('SELECT 999')
    with pytest.raises(ValueError, match='retained_sql_changed'):
        LOCAL.run_queue(path)

@pytest.mark.parametrize('command, expected_flag', [('queue', '--schedule'), ('run', '--continue-from')])
def test_public_cli_exposes_local_recovery_commands(command, expected_flag):
    import subprocess
    import sys
    result = subprocess.run([sys.executable, '-m', 'workpaperbench.current_cli', command, '--help'],
                            cwd=Path(__file__).parents[1], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert expected_flag in result.stdout
