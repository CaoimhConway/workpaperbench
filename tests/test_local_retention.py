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

@pytest.mark.parametrize('kind', ['NonZeroAgentExitCodeError', 'AgentTimeoutError'])
def test_candidate_failure_retains_separate_verdict(tmp_path, kind):
    import json
    from types import SimpleNamespace
    output = tmp_path / 'attempt'
    path = output / 'trials/attempt/verifier/verdict.json'
    path.parent.mkdir(parents=True)
    verdict = {'checks': {'delivery': False, 'financial_answer': None},
               'isolation': {'network_probe_blocked': True, 'network_namespace_none': True,
                             'no_inference_key': True, 'no_docker_socket': True}}
    raw = json.dumps(verdict).encode()
    path.write_bytes(raw)
    receipt = {'attempt_id': 'attempt'}
    local_trial.record_verification(output, receipt,
        SimpleNamespace(exception_type=kind, exception_message='Candidate stopped'))
    assert receipt['status'] == 'candidate_failed'
    assert receipt['candidate_error_type'] == kind
    assert receipt['verdict']['checks']['delivery'] is False
    assert (output / 'verifier.json').read_bytes() == raw


def test_candidate_failure_cannot_bypass_verifier_isolation(tmp_path):
    import json
    from types import SimpleNamespace
    output = tmp_path / 'attempt'
    path = output / 'trials/attempt/verifier/verdict.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'checks': {'delivery': True},
                               'isolation': {'network_probe_blocked': True}}))
    with pytest.raises(ValueError, match='boundary_failed'):
        local_trial.record_verification(output, {'attempt_id': 'attempt'},
            SimpleNamespace(exception_type='NonZeroAgentExitCodeError', exception_message='Stopped'))
    assert not (output / 'verifier.json').exists()

def continuation_fixture(tmp_path, monkeypatch):
    import json
    monkeypatch.setattr(local_trial, 'ROOT', tmp_path)
    previous = tmp_path / '.raw/local-trials/previous'
    (previous / 'raw-sql').mkdir(parents=True)
    sql = b'SELECT 1 AS value'
    (previous / 'raw-sql/result.sql').write_bytes(sql)
    identity = {'task_id': 'workflow-v5-c01', 'task_sha256': 'task',
                'manifest_id': 'manifest', 'scorer_sha256': 'scorer'}
    model = {'id': 'fixture-model', 'sha256': 'weights'}
    profile = {'model': model, 'runtime': {}, 'serving': {},
               'harbor_version': 'pinned', 'hermes_revision': 'pinned',
               'candidate': {'turns': 64, 'generation': {'temperature': 0.7}}}
    prior_profile = {**profile, 'candidate': {**profile['candidate'], 'turns': 24}}
    prior = {**identity, 'inference': True, 'model_configuration': prior_profile,
             'sql_file_sha256': {'result.sql': hashlib.sha256(sql).hexdigest()}}
    (previous / 'receipt.json').write_text(json.dumps(prior))
    session = previous / 'trials/previous/agent/hermes-session.jsonl'
    session.parent.mkdir(parents=True)
    session.write_text(json.dumps({'id': 'native_session', 'model': 'fixture-model', 'messages': []}) + '\n')
    task = tmp_path / 'task'
    (task / 'environment').mkdir(parents=True)
    (task / 'environment/Dockerfile').write_text('FROM fixture\n')
    return task, identity, profile, previous


def test_continuation_restores_only_matching_session_and_sql(tmp_path, monkeypatch):
    task, record, profile, previous = continuation_fixture(tmp_path, monkeypatch)
    session = local_trial.prepare_continuation(task, record, 'previous', profile)
    assert session == 'native_session'
    assert record['continuation']['attempt_id'] == 'previous'
    target = task / 'environment/resume-input'
    assert (target / 'sql/result.sql').read_bytes() == (previous / 'raw-sql/result.sql').read_bytes()
    assert sorted(p.name for p in target.iterdir()) == ['session.jsonl', 'sql']


@pytest.mark.parametrize('changed', ['sql', 'task', 'generation'])
def test_continuation_rejects_changed_inputs(tmp_path, monkeypatch, changed):
    task, record, profile, previous = continuation_fixture(tmp_path, monkeypatch)
    if changed == 'sql':
        (previous / 'raw-sql/result.sql').write_bytes(b'SELECT 2')
    elif changed == 'task':
        record['task_sha256'] = 'other-task'
    else:
        profile['candidate']['generation'] = {'temperature': 1.0}
    with pytest.raises(ValueError, match='continuation_.*_changed'):
        local_trial.prepare_continuation(task, record, 'previous', profile)
