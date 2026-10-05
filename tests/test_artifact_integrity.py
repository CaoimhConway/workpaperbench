"""Bounded authenticated artifact controls, without submitted-code execution."""
import base64
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import collect_results
import native_run


def archive(tmp_path, member=None, update=None):
    (tmp_path / 'config').mkdir()
    slot = {'slot_id': 'final-wp03-A-1', 'campaign': 'final', 'task': 'wp03',
            'arm': 'A', 'repetition': 1, 'split': 'evaluation'}
    (tmp_path / 'config/schedule.json').write_text(json.dumps([slot]))
    (tmp_path / 'config/freeze.json').write_text('{"manifest_id":"test"}')
    record = {**slot, 'freeze_manifest_id': 'test', 'run_id': '5',
              'github_run_attempt': '1', 'commit_sha': 'a' * 40, **(update or {})}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        z.writestr('record.json', json.dumps(record))
        z.writestr(member or 'answer.json', '{}\n')
    data = buffer.getvalue()
    artifact = {'id': 1, 'digest': 'sha256:' + hashlib.sha256(data).hexdigest(),
                'workflow_run': {'id': 5, 'head_sha': 'a' * 40}}
    return data, artifact


@pytest.mark.parametrize('member', ['../answer.json', '/answer.json', 'nested/deeper/answer.json'])
def test_archive_paths_cannot_escape_or_overwrite_inputs(tmp_path, member):
    data, artifact = archive(tmp_path, member)
    before = (tmp_path / 'config/freeze.json').read_bytes()
    with pytest.raises(ValueError, match='archive'):
        collect_results.import_archive(data, artifact, tmp_path)
    assert (tmp_path / 'config/freeze.json').read_bytes() == before
    assert not (tmp_path / 'reports/runs').exists()


@pytest.mark.parametrize('update', [{'task': '../../config'}, {'arm': 'B'}, {'run_id': '6'},
                                    {'commit_sha': 'b' * 40}])
def test_record_identity_is_verified_before_saving(tmp_path, update):
    data, artifact = archive(tmp_path, update=update)
    with pytest.raises(ValueError, match='identity'):
        collect_results.import_archive(data, artifact, tmp_path)
    assert not (tmp_path / 'reports/runs').exists()


def test_archive_digest_and_member_types_are_required(tmp_path):
    data, artifact = archive(tmp_path)
    with pytest.raises(ValueError, match='digest'):
        collect_results.import_archive(data, {**artifact, 'digest': None}, tmp_path)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        info = zipfile.ZipInfo('answer.json')
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        z.writestr(info, '/trusted/reference.json')
    data = buffer.getvalue()
    artifact['digest'] = 'sha256:' + hashlib.sha256(data).hexdigest()
    with pytest.raises(ValueError, match='entry'):
        collect_results.import_archive(data, artifact, tmp_path)


@pytest.mark.parametrize('encode', [lambda b: base64.b64encode(b), lambda b: b.hex().encode(),
                                    lambda b: b.replace(b'-', b'%2D')])
def test_encoded_unknown_credential_pattern_is_withheld(encode):
    synthetic = b'sk-or-v1-' + b'abcdefgh12345678' * 2
    assert native_run.credential_in(encode(synthetic), '')


def test_tool_observations_are_bounded_and_screened(tmp_path):
    key = 'synthetic-private-' + '12345678' * 4
    trajectory = {'steps': [{'message': 'private reasoning excluded',
        'tool_calls': [{'function_name': 'terminal', 'arguments': {'command': 'SELECT 1'}, 'tool_call_id': 'c1'}],
        'observation': {'results': [{'source_call_id': 'c1', 'content': 'returned 1'},
                                     {'source_call_id': 'c2', 'content': key}]}}]}
    source = tmp_path / 'trajectory.json'
    source.write_text(json.dumps(trajectory))
    destination = tmp_path / 'tools.json'
    state = native_run.save_tool_evidence(source, destination, key)
    saved = json.loads(destination.read_text())
    assert saved['observations'] == [{'source_call_id': 'c1', 'content': 'returned 1'}]
    assert state['omitted_items'] == 1
    assert key not in destination.read_text()
    assert 'private reasoning excluded' not in destination.read_text()


@pytest.mark.parametrize('job,expected', [
    ({'status': 'queued'}, 'never_started'),
    ({'status': 'completed', 'conclusion': 'cancelled', 'runner_id': 1}, 'cancelled_exposure_unknown'),
    ({'status': 'completed', 'conclusion': 'success', 'runner_id': 1}, 'completed_evidence_unavailable'),
    ({'status': 'completed', 'conclusion': 'failure', 'runner_id': 1,
      'steps': [{'name': 'Capped budget check and one native live slot', 'conclusion': 'skipped'}]}, 'setup_failed'),
    ({'status': 'completed', 'conclusion': 'failure', 'runner_id': 1}, 'started_exposure_unknown'),
])
def test_missing_evidence_is_reconciled_from_actual_job_state(job, expected):
    assert collect_results.missing_state(job) == expected


@pytest.mark.parametrize('name', ['config/runtime.json', 'sources/wp03.json', 'tasks/wp03/instruction.md'])
def test_correction_registry_cannot_authorize_experiment_inputs(tmp_path, name):
    import shutil
    import subprocess
    (tmp_path / 'scripts').mkdir()
    shutil.copyfile(ROOT / 'scripts/audit.py', tmp_path / 'scripts/audit.py')
    target = tmp_path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('original')
    freeze = tmp_path / 'config/freeze.json'
    freeze.parent.mkdir(exist_ok=True)
    freeze.write_text(json.dumps({'manifest_id': 'test', 'hashes': {name: hashlib.sha256(b'original').hexdigest()}}))
    target.write_text('changed experiment')
    review = {'original_manifest_id': 'test',
              'original_freeze_sha256': hashlib.sha256(freeze.read_bytes()).hexdigest(),
              'correction_hashes': {name: hashlib.sha256(target.read_bytes()).hexdigest()}}
    (tmp_path / 'config/review.json').write_text(json.dumps(review))
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(['git', 'add', '.'], cwd=tmp_path, check=True)
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/audit.py')],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1
    assert 'candidate_or_reference_changed' in result.stdout
    assert 'unauthorized_correction_path' in result.stdout
