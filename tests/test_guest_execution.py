import argparse
import asyncio
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import guest_bench
import local_trial


def configuration(tmp_path):
    spec = json.loads((ROOT / 'config/external-model.example.json').read_text())
    spec['model']['revision'] = 'test-weights-revision'
    spec['runtime'] = {'name': 'test-server', 'version': 'test-version'}
    path = tmp_path / 'profile.json'
    path.write_text(json.dumps(spec))
    return path, spec


@pytest.mark.parametrize('field,value', [
    ('turns', 0), ('turns', 91), ('turns', True), ('wall_seconds', -1), ('wall_seconds', 21601),
])
def test_guest_rejects_invalid_native_budgets(tmp_path, field, value):
    path, spec = configuration(tmp_path)
    spec['candidate'][field] = value
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match='execution_budget'):
        local_trial.external_configuration(path)


@pytest.mark.parametrize('change', ['endpoint', 'credentials', 'generation', 'version', 'token_limit'])
def test_guest_rejects_unbounded_or_unpinned_route(tmp_path, change):
    path, spec = configuration(tmp_path)
    if change == 'endpoint':
        spec['serving']['base_url'] = 'https://example.com/v1'
    elif change == 'credentials':
        spec['serving']['api_key'] = 'do-not-pass-credentials'
    elif change == 'generation':
        spec['candidate']['generation']['max_tokens'] = 1.5
    elif change == 'version':
        spec['harbor_version'] = 'unreviewed'
    else:
        spec['candidate']['generation']['max_tokens'] = spec['serving']['context'] + 1
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError):
        local_trial.external_configuration(path)


def test_guest_native_arguments_preserve_declared_budget(tmp_path):
    path, spec = configuration(tmp_path)
    args = argparse.Namespace(dataset='workflow-v7', task='c01', attempt='external-1')
    trial = guest_bench.trial_arguments(args, path)
    assert trial.wall == spec['candidate']['wall_seconds']
    assert trial.turns == spec['candidate']['turns']
    assert trial.model == spec['model']['id']
    assert trial.execution_profile == 'isolated-linux'
    assert not trial.transport_smoke


def test_guest_rejects_unconfigured_example():
    with pytest.raises(ValueError, match='configuration_identity'):
        local_trial.external_configuration(ROOT / 'config/external-model.example.json')


def test_low_level_rejects_held_out_inference_before_native_setup(tmp_path, monkeypatch):
    path, spec = configuration(tmp_path)
    monkeypatch.setattr(local_trial, 'ROOT', tmp_path)
    monkeypatch.setattr(local_trial, 'clean_environment', lambda: None)
    monkeypatch.setattr(local_trial.platform, 'machine', lambda: 'x86_64')
    monkeypatch.setattr(local_trial, 'load', lambda *args: ({}, {'split': 'evaluation'}, tmp_path))
    args = argparse.Namespace(dataset='workflow-v7', task='c09', attempt='external-1')
    with pytest.raises(ValueError, match='must_not_see_held_out'):
        asyncio.run(local_trial.run(guest_bench.trial_arguments(args, path)))
    assert not (tmp_path / '.raw').exists()


def test_profile_budget_mismatch_rejected_before_native_setup(tmp_path, monkeypatch):
    path, _ = configuration(tmp_path)
    monkeypatch.setattr(local_trial, 'ROOT', tmp_path)
    monkeypatch.setattr(local_trial, 'clean_environment', lambda: None)
    monkeypatch.setattr(local_trial.platform, 'machine', lambda: 'x86_64')
    monkeypatch.setattr(local_trial, 'load', lambda *args: ({}, {'split': 'development'}, tmp_path))
    args = guest_bench.trial_arguments(argparse.Namespace(dataset='workflow-v7', task='c01', attempt='external-1'), path)
    args.turns += 1
    with pytest.raises(ValueError, match='effective_model_configuration_mismatch'):
        asyncio.run(local_trial.run(args))
    assert not (tmp_path / '.raw').exists()


@pytest.mark.parametrize('installer', ['missing', 'changed'])
def test_installer_failure_retains_infrastructure_receipt(tmp_path, monkeypatch, installer):
    path, _ = configuration(tmp_path)
    source = tmp_path / 'source'
    source.mkdir()
    for name in ('scripts/local_trial.py', 'scripts/fresh_replay.py', 'scripts/fix_native_version.py',
                 'scripts/native_run.py', 'config/runtime.json'):
        target = tmp_path / name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    if installer == 'changed':
        (tmp_path / '.local').mkdir()
        (tmp_path / '.local/hermes-install.sh').write_text('unreviewed installer')
    manifest = {'manifest_id': 'fixture-manifest', 'scorer_version': 'fixture', 'scorer_sha256': 'fixture-scorer'}
    spec = {'split': 'development', 'task_id': 'workflow-v7-c01', 'task_sha256': 'fixture-task'}
    monkeypatch.setattr(local_trial, 'ROOT', tmp_path)
    monkeypatch.setattr(local_trial, 'clean_environment', lambda: None)
    monkeypatch.setattr(local_trial.platform, 'machine', lambda: 'x86_64')
    monkeypatch.setattr(local_trial, 'load', lambda *args: (manifest, spec, source))
    retained = []
    original_retention = local_trial.retain_artifacts

    def retain(*args):
        retained.append(args[2]['attempt_id'])
        original_retention(*args)

    monkeypatch.setattr(local_trial, 'retain_artifacts', retain)
    args = guest_bench.trial_arguments(argparse.Namespace(dataset='workflow-v7', task='c01', attempt='external-1'), path)
    expected = 'unsafe_or_missing_file' if installer == 'missing' else 'external_pinned_installer_changed'
    with pytest.raises(ValueError, match=expected):
        asyncio.run(local_trial.run(args))
    output = tmp_path / '.raw/local-trials/external-1'
    receipt = json.loads((output / 'receipt.json').read_text())
    assert receipt['status'] == 'infrastructure_failed'
    assert receipt['error_type'] == 'ValueError'
    assert receipt['error'] == expected
    assert receipt['finished_at']
    assert 'verdict' not in receipt
    assert not (output / 'trials').exists()
    assert retained == ['external-1']


def test_public_guest_cli_exposes_native_commands():
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'workpaperbench.current_cli', 'guest', '--help'],
                            cwd=ROOT, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert '{preflight,run,grade,smoke,report}' in result.stdout


def test_scripted_fixture_requires_real_tool_result():
    from io import BytesIO
    observations = []
    output = []
    handler = object.__new__(guest_bench.FixtureHandler)
    handler.path = '/v1/chat/completions'
    handler.observations = observations
    handler.send = lambda value, *args: output.append(value)
    first = {'model': 'deterministic-harness-fixture',
             'tools': [{'function': {'name': 'terminal'}}],
             'messages': [{'role': 'user', 'content': 'WPB_TRANSPORT_OK'}]}
    raw = json.dumps(first).encode()
    handler.headers = {'Content-Length': str(len(raw))}
    handler.rfile = BytesIO(raw)
    handler.do_POST()
    assert output[-1]['choices'][0]['finish_reason'] == 'tool_calls'
    assert not observations[-1]['tool_result_observed']
    first['messages'].append({'role': 'tool', 'tool_call_id': 'wpb-fixture-call', 'content': 'WPB_TRANSPORT_OK'})
    raw = json.dumps(first).encode()
    handler.headers = {'Content-Length': str(len(raw))}
    handler.rfile = BytesIO(raw)
    handler.do_POST()
    assert output[-1]['choices'][0]['finish_reason'] == 'stop'
    assert observations[-1]['tool_result_observed']
