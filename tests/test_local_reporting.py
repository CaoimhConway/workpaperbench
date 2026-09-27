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
