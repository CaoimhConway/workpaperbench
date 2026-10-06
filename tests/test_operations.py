"""Regression controls for the published campaign's setup and collection failure."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import attempts
import collect_results
import fresh_replay
import native_run
import operations_review
import select_slots
from test_real_campaign import fixture_dataset


@pytest.mark.parametrize('status', [500, 502, 503, 504])
@pytest.mark.parametrize('message', ['gh: HTTP {status}', 'gh: failure (HTTP {status})'])
def test_transient_read_failure_retries_then_returns_json(monkeypatch, status, message):
    calls, sleeps = [], []

    def read(command, **kwargs):
        calls.append(command)
        assert kwargs['stderr'] == subprocess.PIPE
        if len(calls) == 1:
            raise subprocess.CalledProcessError(1, command, stderr=message.format(status=status).encode())
        return b'{"jobs": []}'

    monkeypatch.setattr(select_slots.subprocess, 'check_output', read)
    monkeypatch.setattr(select_slots.time, 'sleep', sleeps.append)
    assert select_slots.api('repos/example/project/actions/runs/1/jobs') == {'jobs': []}
    assert len(calls) == 2
    assert all(c[1:4] == ['api', '--method', 'GET'] for c in calls)
    assert sleeps == [1]


@pytest.mark.parametrize('status,count', [(500, 3), (401, 1), (403, 1), (429, 1)])
def test_history_read_failure_remains_closed_and_bounded(monkeypatch, status, count):
    calls, sleeps = [], []

    def read(command, **kwargs):
        calls.append(command)
        raise subprocess.CalledProcessError(1, command, stderr=f'gh: failure (HTTP {status})'.encode())

    monkeypatch.setattr(select_slots.subprocess, 'check_output', read)
    monkeypatch.setattr(select_slots.time, 'sleep', sleeps.append)
    with pytest.raises(subprocess.CalledProcessError):
        select_slots.api('repos/example/project/actions/runs/1/jobs')
    assert len(calls) == count
    assert sleeps == ([1, 2] if count == 3 else [])


def test_invalid_api_json_is_not_retried(monkeypatch):
    calls = []
    monkeypatch.setattr(select_slots.subprocess, 'check_output',
                        lambda *args, **kwargs: calls.append(args) or b'not JSON')
    with pytest.raises(json.JSONDecodeError):
        select_slots.api('repos/example/project/actions/runs/1/jobs')
    assert len(calls) == 1


def test_real_history_skips_unrelated_jobs_and_preserves_prior_attempt(monkeypatch):
    manifest_id = 'real-v1-example'
    run = {'id': 3, 'display_title': f'WPB::{manifest_id}::final'}
    runs = [{'id': 1, 'display_title': 'legacy run'},
            {'id': 2, 'display_title': 'WPB::other::final'}, run]
    job = {'id': 10, 'name': 'pair-final-wp07-A-1--final-wp07-B-1',
           'status': 'completed', 'conclusion': 'failure', 'runner_id': 42,
           'run_attempt': 1, 'started_at': '2026-10-06T00:00:00Z'}
    paths = []

    def pages(path, key):
        paths.append(path)
        if key == 'workflow_runs':
            return iter(runs)
        assert '/runs/3/jobs' in path
        return iter([job, {**job, 'id': 11, 'run_attempt': 2}])

    monkeypatch.setattr(select_slots, 'pages', pages)
    monkeypatch.setenv('GITHUB_RUN_ID', '3')
    monkeypatch.setenv('GITHUB_RUN_ATTEMPT', '2')
    history = select_slots.history('final', manifest_id)
    assert set(history) == {'final-wp07-A-1', 'final-wp07-B-1'}
    assert all(value['job_id'] == 10 for value in history.values())
    assert len(paths) == 2


def pair_archive(records, manifest_id, campaign):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for record in records:
            archive.writestr(record['slot_id'] + '/record.json', json.dumps(record))
    data = buffer.getvalue()
    return data, {'id': 91, 'digest': 'sha256:' + hashlib.sha256(data).hexdigest(),
                  'declared_slots': [record['slot_id'] for record in records],
                  'manifest_id': manifest_id, 'campaign': campaign,
                  'workflow_run': {'id': 51, 'head_sha': 'a' * 40, 'run_attempt': 1}}


@pytest.mark.parametrize('campaign', ['final', 'pilot'])
def test_real_setup_failure_receipts_round_trip_with_completed_pair_member(tmp_path, monkeypatch, campaign):
    manifest, final, pilot = fixture_dataset(tmp_path)
    manifest_id = manifest['manifest_id'] if campaign == 'final' else 'real-v1-development'
    slots = (final if campaign == 'final' else pilot)[:2]
    identifiers = [slot['slot_id'] for slot in slots]
    monkeypatch.setattr(attempts, 'ROOT', tmp_path)
    monkeypatch.setattr(select_slots, 'ROOT', tmp_path)
    monkeypatch.setattr(select_slots, 'history', lambda *args: {})
    monkeypatch.setenv('GITHUB_RUN_ATTEMPT', '1')
    monkeypatch.setenv('GITHUB_RUN_ID', '51')
    monkeypatch.setenv('GITHUB_SHA', 'a' * 40)
    attempts.receipt(campaign, manifest_id, identifiers)
    first_path = attempts.record_directory(manifest_id, identifiers[0]) / 'record.json'
    first = json.loads(first_path.read_text())
    first.update(status='complete', verdict={'checks': {'format': True}})
    attempts.write(first_path, first)
    attempts.finalize(manifest_id, identifiers)
    records = [json.loads((attempts.record_directory(manifest_id, identifier) / 'record.json').read_text())
               for identifier in identifiers]
    assert records[0]['status'] == 'complete'
    assert records[1]['status'] == 'infra_failed'
    assert records[1]['verdict'] is None
    assert all(r['dataset_manifest_id'] == manifest['manifest_id'] for r in records)
    assert all(r['dataset_id'] == 'real-v1' for r in records)
    data, artifact = pair_archive(records, manifest_id, campaign)
    shutil.rmtree(tmp_path / 'reports')
    assert collect_results.import_archive(data, artifact, tmp_path) == identifiers
    assert all((attempts.record_directory(manifest_id, identifier) / 'artifact-audit.json').is_file()
               for identifier in identifiers)


def test_invalid_second_member_cannot_leave_a_partial_import(tmp_path):
    manifest, slots, _ = fixture_dataset(tmp_path)
    records = [{**slot, 'freeze_manifest_id': manifest['manifest_id'],
                'dataset_manifest_id': manifest['manifest_id'], 'run_id': '51',
                'github_run_attempt': '1', 'commit_sha': 'a' * 40} for slot in slots[:2]]
    del records[1]['dataset_manifest_id']
    data, artifact = pair_archive(records, manifest['manifest_id'], 'final')
    with pytest.raises(ValueError, match='artifact_dataset_identity_mismatch'):
        collect_results.import_archive(data, artifact, tmp_path)
    assert not (tmp_path / 'reports').exists()


def test_original_byte_hash_failure_creates_no_destination(tmp_path):
    from test_artifact_integrity import archive
    data, artifact = archive(tmp_path, member='answer.raw.txt', update={'raw_sha256': '0' * 64})
    with pytest.raises(ValueError, match='original_bytes_hash_mismatch'):
        collect_results.import_archive(data, artifact, tmp_path)
    assert not (tmp_path / 'reports').exists()


def test_two_archive_groups_cannot_overwrite_the_same_slot(tmp_path):
    from test_artifact_integrity import archive
    data, artifact = archive(tmp_path)
    with zipfile.ZipFile(io.BytesIO(data)) as original:
        record = original.read('record.json')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as repeated:
        repeated.writestr('record.json', record)
        repeated.writestr('final-wp03-A-1/record.json', record)
    data = buffer.getvalue()
    artifact['digest'] = 'sha256:' + hashlib.sha256(data).hexdigest()
    with pytest.raises(ValueError, match='duplicate_archive_slot'):
        collect_results.import_archive(data, artifact, tmp_path)
    assert not (tmp_path / 'reports').exists()


def correction(root, manifest, name):
    freeze = root / 'datasets/real-v1/manifest.json'
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b'operational correction\n')
    review = {'original_manifest_id': manifest['manifest_id'],
              'original_manifest_sha256': hashlib.sha256(freeze.read_bytes()).hexdigest(),
              'correction_hashes': {name: hashlib.sha256(target.read_bytes()).hexdigest()}}
    (root / 'datasets/real-v1/operations-review.json').write_text(json.dumps(review))
    return review


def test_reviewed_operations_allow_key_free_checks_but_not_paid_launch(tmp_path):
    manifest, _, _ = fixture_dataset(tmp_path)
    correction(tmp_path, manifest, 'scripts/select_slots.py')
    assert native_run.frozen_inputs(manifest['manifest_id'], tmp_path, reviewed_operations=True) == manifest
    with pytest.raises(ValueError, match='freeze_hash_mismatch'):
        native_run.frozen_inputs(manifest['manifest_id'], tmp_path)
    (tmp_path / 'datasets/real-v1/tasks/wp01/environment/data.sqlite').write_bytes(b'changed data')
    with pytest.raises(ValueError, match='freeze_hash_mismatch'):
        native_run.frozen_inputs(manifest['manifest_id'], tmp_path, reviewed_operations=True)


@pytest.mark.parametrize('name', ['config/runtime.json', 'workpaperbench/grading.py',
                                 'datasets/real-v1/tasks/wp01/tests/gold.json',
                                 'datasets/real-v1/captures/filing.html'])
def test_operational_review_cannot_authorize_experiment_or_scorer_changes(tmp_path, name):
    manifest, _, _ = fixture_dataset(tmp_path)
    correction(tmp_path, manifest, name)
    with pytest.raises(ValueError, match='unauthorized_operations_correction'):
        operations_review.reviewed_hashes(manifest, tmp_path)


def test_operational_review_binds_exact_manifest_bytes(tmp_path):
    manifest, _, _ = fixture_dataset(tmp_path)
    correction(tmp_path, manifest, 'scripts/select_slots.py')
    freeze = tmp_path / 'datasets/real-v1/manifest.json'
    freeze.write_bytes(freeze.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='operations_review_manifest_mismatch'):
        operations_review.reviewed_hashes(manifest, tmp_path)


def test_published_manifest_remains_replayable_and_closed_to_new_paid_trials():
    manifest, _, tasks = fresh_replay.load_real_manifest(ROOT)
    assert manifest['manifest_id'] == 'real-v1-76d0ba6152ff'
    assert len(tasks) == 8
    with pytest.raises(ValueError, match='freeze_hash_mismatch'):
        native_run.frozen_inputs(manifest['manifest_id'], ROOT)
