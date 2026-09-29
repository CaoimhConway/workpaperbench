import hashlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import local_trial


def artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(local_trial, 'ROOT', tmp_path)
    output = tmp_path / 'attempt'
    directory = output / 'trials/attempt/artifacts/logs/artifacts'
    directory.mkdir(parents=True)
    return output, directory, {'attempt_id': 'attempt'}


def test_sql_without_answer_is_retained_exactly(tmp_path, monkeypatch):
    output, directory, receipt = artifacts(tmp_path, monkeypatch)
    raw = b'SELECT 1 AS value\n'
    (directory / 'partial.sql').write_bytes(raw)
    local_trial.retain_artifacts(output, 'workflow-v4', receipt)
    assert (output / 'raw-sql/partial.sql').read_bytes() == raw
    assert receipt['sql_file_sha256'] == {'partial.sql': hashlib.sha256(raw).hexdigest()}
    assert 'raw_answer_sha256' not in receipt
    assert not (output / 'answer.json').exists()


def test_malformed_json_does_not_drop_actual_sql(tmp_path, monkeypatch):
    output, directory, receipt = artifacts(tmp_path, monkeypatch)
    raw = b'{"unfinished":'
    (directory / 'answer.json').write_bytes(raw)
    (directory / 'partial.sql').write_bytes(b'SELECT 2\n')
    local_trial.retain_artifacts(output, 'workflow-v4', receipt)
    assert (output / 'raw-answer.json').read_bytes() == raw
    assert (output / 'raw-sql/partial.sql').read_bytes() == b'SELECT 2\n'
    assert receipt['normalized_answer_sha256'] is None


def test_sql_symlink_is_rejected_without_an_answer(tmp_path, monkeypatch):
    output, directory, receipt = artifacts(tmp_path, monkeypatch)
    target = tmp_path / 'outside.sql'
    target.write_bytes(b'SELECT 3')
    (directory / 'partial.sql').symlink_to(target)
    with pytest.raises(ValueError, match='symlink'):
        local_trial.retain_artifacts(output, 'workflow-v4', receipt)
    assert not (output / 'raw-sql/partial.sql').exists()
