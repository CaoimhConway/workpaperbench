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
    spec['serving'].pop('api_key_env', None)
    spec['serving']['base_url'] = 'http://10.88.0.1:19090/v1'
    path = tmp_path / 'profile.json'
    path.write_text(json.dumps(spec))
    return path, spec


@pytest.mark.parametrize('field,value', [
    ('turns', 0), ('turns', True), ('wall_seconds', -1), ('wall_seconds', 0),
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
        spec['serving']['base_url'] = 'https://user:password@example.com/v1'
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


def test_local_profile_still_rejects_held_out_inference(tmp_path, monkeypatch):
    path, spec = configuration(tmp_path)
    spec['execution_profile'] = 'local-lima'
    path.write_text(json.dumps(spec))
    monkeypatch.setattr(local_trial, 'ROOT', tmp_path)
    monkeypatch.setattr(local_trial, 'clean_environment', lambda **kwargs: None)
    monkeypatch.setattr(local_trial.platform, 'machine', lambda: 'x86_64')
    monkeypatch.setattr(local_trial, 'load', lambda *args: ({}, {'split': 'evaluation'}, tmp_path))
    args = argparse.Namespace(dataset='workflow-v7', task='c09', attempt='external-1',
                              configuration=path, model=spec['model']['id'], turns=24, wall=3600)
    with pytest.raises(ValueError, match='must_not_see_held_out'):
        asyncio.run(local_trial.run(args))
    assert not (tmp_path / '.raw').exists()


def test_profile_budget_mismatch_rejected_before_native_setup(tmp_path, monkeypatch):
    path, _ = configuration(tmp_path)
    monkeypatch.setattr(local_trial, 'ROOT', tmp_path)
    monkeypatch.setattr(local_trial, 'clean_environment', lambda **kwargs: None)
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
    (source / 'task.toml').write_text('allowed_hosts = ["172.17.0.1"]\n')
    for name in ('scripts/local_trial.py', 'scripts/fresh_replay.py', 'scripts/fix_native_version.py',
                 'scripts/native_run.py', 'config/runtime.json'):
        target = tmp_path / name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    if installer == 'changed':
        (tmp_path / '.local').mkdir()
        (tmp_path / '.local/hermes-install.sh').write_text('unreviewed installer')
    manifest = {'manifest_id': 'fixture-manifest', 'scorer_version': 'fixture', 'scorer_sha256': 'fixture-scorer'}
    spec = {'split': 'evaluation', 'task_id': 'workflow-v7-c01', 'task_sha256': 'fixture-task'}
    monkeypatch.setattr(local_trial, 'ROOT', tmp_path)
    monkeypatch.setattr(local_trial, 'clean_environment', lambda **kwargs: None)
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
    assert receipt['task_split'] == 'evaluation'
    assert receipt['external_service_spend_usd'] is None
    assert 'verdict' not in receipt
    assert not (output / 'trials').exists()
    assert retained == ['external-1']


def test_public_guest_cli_exposes_native_commands():
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'workpaperbench.current_cli', 'guest', '--help'],
                            cwd=ROOT, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert '{preflight,list,batch,run,grade,smoke,report}' in result.stdout


def test_scripted_fixture_requires_real_tool_result():
    from io import BytesIO
    observations = []
    output = []
    handler = object.__new__(guest_bench.FixtureHandler)
    handler.path = '/v1/chat/completions'
    handler.credential = 'fixture-token'
    handler.observations = observations
    handler.send = lambda value, *args: output.append(value)
    first = {'model': 'deterministic-harness-fixture',
             'tools': [{'function': {'name': 'terminal'}}],
             'messages': [{'role': 'user', 'content': 'WPB_TRANSPORT_OK'}]}
    raw = json.dumps(first).encode()
    handler.headers = {'Content-Length': str(len(raw)), 'Authorization': 'Bearer fixture-token'}
    handler.rfile = BytesIO(raw)
    handler.do_POST()
    assert output[-1]['choices'][0]['finish_reason'] == 'tool_calls'
    assert not observations[-1]['tool_result_observed']
    first['messages'].append({'role': 'tool', 'tool_call_id': 'wpb-fixture-call', 'content': 'WPB_TRANSPORT_OK'})
    raw = json.dumps(first).encode()
    handler.headers = {'Content-Length': str(len(raw)), 'Authorization': 'Bearer fixture-token'}
    handler.rfile = BytesIO(raw)
    handler.do_POST()
    assert output[-1]['choices'][0]['finish_reason'] == 'stop'
    assert observations[-1]['tool_result_observed']


@pytest.mark.parametrize('url', [
    'file:///tmp/secret', 'https://user:secret@example.com/v1', 'https://example.com/v1?key=secret',
    'https://example.com/v1#secret', 'http://example.com:0/v1', 'http://example.com:65536/v1',
    'https://example.com\n/v1', 'https://bad%20host/v1',
])
def test_model_endpoint_rejects_unsafe_urls(url):
    with pytest.raises(ValueError):
        local_trial.endpoint_url(url)


def test_endpoint_rules_pin_only_resolved_addresses_and_configured_port(monkeypatch):
    monkeypatch.setattr(local_trial.socket, 'getaddrinfo', lambda *args, **kwargs: [
        (2, 1, 6, '', ('10.88.0.1', 19443)), (10, 1, 6, '', ('fd00::2', 19443, 0, 0))])
    endpoint = local_trial.resolve_endpoint('https://models.example.test:19443/v1')
    assert endpoint == {'hostname': 'models.example.test', 'port': 19443, 'addresses': ['10.88.0.1', 'fd00::2']}
    rules = local_trial.endpoint_rules(endpoint)
    assert 'ip daddr 10.88.0.1 tcp dport 19443 accept' in rules
    assert 'ip6 daddr fd00::2 tcp dport 19443 accept' in rules
    assert 'ip daddr 127.0.0.11 counter drop' in rules
    assert '{ icmp, ipv6-icmp } counter drop' in rules
    ndp = 'ip6 hoplimit 255 icmpv6 type { nd-neighbor-solicit, nd-neighbor-advert } accept'
    assert ndp in rules
    assert rules.index(ndp) < rules.index('{ icmp, ipv6-icmp } counter drop')
    assert 'echo-request' not in rules and 'nd-router-advert' not in rules
    assert '172.17.0.1' not in rules
    assert 'policy drop' in rules


@pytest.mark.parametrize('value', [None, '', ' ', 'secret\nline', 'secret key'])
def test_missing_or_invalid_named_key_fails_before_model_execution(tmp_path, monkeypatch, value):
    _, spec = configuration(tmp_path)
    spec['serving']['api_key_env'] = 'WPB_TEST_KEY'
    monkeypatch.delenv('WPB_TEST_KEY', raising=False)
    if value is not None:
        monkeypatch.setenv('WPB_TEST_KEY', value)
    with pytest.raises(ValueError, match='api_key_missing_or_invalid'):
        local_trial.model_credential(spec)


def test_optional_generation_controls_and_larger_declared_budgets(tmp_path):
    path, spec = configuration(tmp_path)
    spec['candidate'].update(turns=128, wall_seconds=86400, generation={'max_tokens': 32768})
    spec['serving']['context'] = 1048576
    spec['serving']['base_url'] = 'https://api.example.test/custom/v1'
    path.write_text(json.dumps(spec))
    parsed, _ = local_trial.external_configuration(path)
    assert parsed == spec


@pytest.mark.parametrize('identifier', ['qwen:latest', 'team/model@version-1'])
def test_compatible_model_aliases_and_undisclosed_revision(tmp_path, identifier):
    path, spec = configuration(tmp_path)
    spec['model'] = {'id': identifier, 'revision': 'not reported by server'}
    path.write_text(json.dumps(spec))
    parsed, _ = local_trial.external_configuration(path)
    assert parsed['model'] == spec['model']


def test_external_environment_cleanup_does_not_require_owner_marker(monkeypatch):
    monkeypatch.setattr(local_trial.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(local_trial.os, 'environ', {'PATH': '/bin', 'WPB_TEST_KEY': 'secret', 'GH_TOKEN': 'unrelated'})
    monkeypatch.setattr(Path, 'is_file', lambda self: False)
    local_trial.clean_environment(external=True)
    assert dict(local_trial.os.environ) == {'PATH': '/bin'}


def test_external_cleanup_preserves_controller_docker_settings_only(monkeypatch):
    values = {name: 'controller-only-' + name for name in local_trial.DOCKER_CLIENT_ENV}
    monkeypatch.setattr(local_trial.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(local_trial.os, 'environ', {**values, 'PATH': '/bin',
                        'SSH_AUTH_SOCK': '/private/ssh-agent', 'GH_TOKEN': 'unrelated',
                        'WPB_TEST_KEY': 'model-key-captured-separately'})
    local_trial.clean_environment(external=True)
    assert dict(local_trial.os.environ) == {**values, 'PATH': '/bin'}


def test_native_candidate_does_not_inherit_controller_docker_settings(tmp_path, monkeypatch):
    pytest.importorskip('harbor')
    from importlib.metadata import distribution
    from types import ModuleType
    original = Path(distribution('harbor').locate_file('harbor/agents/installed/hermes.py'))
    source = local_trial.local_hermes_source(original.read_bytes(), 2,
        {'max_tokens': 100, '_context': 4096}, external=True)
    module = ModuleType('_wpb_native_environment_test')
    monkeypatch.setitem(sys.modules, module.__name__, module)
    exec(compile(source, str(original), 'exec'), module.__dict__)
    for name in local_trial.DOCKER_CLIENT_ENV:
        monkeypatch.setenv(name, 'controller-only-' + name)
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-native-key')
    monkeypatch.setenv('OPENAI_BASE_URL', 'https://model.example.test/v1')
    logs = tmp_path / 'native-logs'
    logs.mkdir()
    agent = module.Hermes(logs_dir=logs, model_name='custom/fixture', version='fixture')
    captured = {}

    class Captured(Exception):
        pass

    async def capture(environment, command, **kwargs):
        captured.update(command=command, env=kwargs.get('env'))
        raise Captured

    monkeypatch.setattr(agent, 'exec_as_agent', capture)
    with pytest.raises(Captured):
        asyncio.run(agent.run('fixture', None, None))
    assert not (set(captured['env']) & local_trial.DOCKER_CLIENT_ENV)
    assert captured['env']['OPENAI_API_KEY'] == 'synthetic-native-key'
    assert 'synthetic-native-key' not in captured['command']
    assert all('controller-only-' + name not in captured['command'] for name in local_trial.DOCKER_CLIENT_ENV)


def test_all_task_selection_includes_evaluation_split(monkeypatch):
    monkeypatch.setattr(guest_bench, 'load', lambda *args: {'tasks': {
        'a01': {'split': 'development'}, 'a03': {'split': 'evaluation'}}})
    assert guest_bench.selected_tasks('fixture', split='all') == ['a01', 'a03']
    assert guest_bench.selected_tasks('fixture', split='evaluation') == ['a03']
    assert guest_bench.selected_tasks('fixture', tasks=['a03', 'a01']) == ['a03', 'a01']
    with pytest.raises(ValueError, match='invalid_task_selection'):
        guest_bench.selected_tasks('fixture', tasks=['a03', 'a03'])


def test_authenticated_batch_preserves_key_in_memory_across_cleaned_attempts(tmp_path, monkeypatch):
    path, spec = configuration(tmp_path)
    spec['serving']['api_key_env'] = 'WPB_TEST_KEY'
    path.write_text(json.dumps(spec))
    sentinel = 'synthetic-batch-token-not-a-provider-key'
    monkeypatch.setattr(local_trial.os, 'environ', {'PATH': '/bin', 'WPB_TEST_KEY': sentinel})
    monkeypatch.setattr(local_trial.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(guest_bench, 'ROOT', tmp_path)
    monkeypatch.setattr(guest_bench, 'preflight', lambda: None)
    monkeypatch.setattr(guest_bench, 'load', lambda *args: {'tasks': {
        'a01': {'split': 'development'}, 'a03': {'split': 'evaluation'}}})
    calls = []

    async def fake_run(args, credential=None):
        calls.append((args.task, credential, 'WPB_TEST_KEY' in local_trial.os.environ))
        local_trial.clean_environment(external=True)
        directory = tmp_path / '.raw/local-trials' / args.attempt
        directory.mkdir(parents=True)
        (directory / 'receipt.json').write_text(json.dumps({
            'task_id': 'fixture-' + args.task, 'status': 'candidate_failed' if args.task == 'a01' else 'verified'}))

    monkeypatch.setattr(guest_bench, 'run', fake_run)
    args = argparse.Namespace(dataset='fixture', tasks=None, split='all', profile=path, attempt='batch-1')
    guest_bench.batch(args)
    assert calls == [('a01', sentinel, True), ('a03', sentinel, False)]
    summary = json.loads((tmp_path / '.raw/local-trials/batch-1-batch.json').read_text())
    assert summary['status'] == 'completed'
    assert len(summary['attempts']) == 2
    assert all(sentinel.encode() not in file.read_bytes() for file in tmp_path.rglob('*') if file.is_file())
    with pytest.raises(ValueError, match='already_exists'):
        monkeypatch.setitem(local_trial.os.environ, 'WPB_TEST_KEY', sentinel)
        guest_bench.batch(args)


def test_secret_redaction_handles_json_escaped_values():
    secret = 'synthetic"\\token'
    value = {'error': 'failed: ' + secret, 'details': [secret]}
    assert local_trial.redact_secret(value, secret) == {'error': 'failed: [redacted]', 'details': ['[redacted]']}


def test_retained_artifact_cannot_copy_arbitrary_model_key(tmp_path, monkeypatch):
    monkeypatch.setattr(local_trial, 'ROOT', tmp_path)
    output = tmp_path / 'attempt'
    artifact = output / 'trials/attempt/artifacts/logs/artifacts/answer.json'
    artifact.parent.mkdir(parents=True)
    artifact.write_text('{"token": "synthetic-custom-token"}')
    with pytest.raises(ValueError, match='credential_in_retained_artifact'):
        local_trial.retain_artifacts(output, 'workflow-v8', {'attempt_id': 'attempt'}, 'synthetic-custom-token')
    assert not (output / 'raw-answer.json').exists()


@pytest.mark.parametrize('prefix,key', [('', 'sensitive-token-' + 'x' * 800), ('error-' + 'x' * 480, 'sensitive-token-' + 'y' * 80)])
def test_errors_redact_complete_key_before_truncation(prefix, key):
    result = local_trial.error_text(prefix + key + '-suffix', key)
    assert 'sensitive-token-' not in result
    assert len(result) <= 500
    assert result == (prefix + '[redacted]-suffix')[:500]


def test_retention_failure_overrides_verified_receipt_and_fails_batch(tmp_path, monkeypatch):
    import builtins
    from types import SimpleNamespace
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'task.toml').write_text('allowed_hosts = ["172.17.0.1"]\n')
    for name in ('scripts/local_trial.py', 'scripts/fresh_replay.py', 'scripts/fix_native_version.py',
                 'scripts/native_run.py', 'config/runtime.json'):
        target = tmp_path / name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    manifest = {'manifest_id': 'fixture', 'scorer_version': 'fixture', 'scorer_sha256': 'fixture'}
    task_spec = {'task_id': 'workflow-v8-a01', 'task_sha256': 'fixture', 'split': 'evaluation'}
    monkeypatch.setattr(local_trial, 'ROOT', tmp_path)
    monkeypatch.setattr(local_trial, 'clean_environment', lambda **kwargs: None)
    monkeypatch.setattr(local_trial, 'load', lambda *args: (manifest, task_spec, source))

    class Trial:
        @classmethod
        async def create(cls, config):
            return cls()

        def add_hook(self, *args):
            pass

        async def run(self):
            return SimpleNamespace(exception_info=None)

    native = {
        'harbor.models.trial.config': SimpleNamespace(TrialConfig=SimpleNamespace(model_validate=lambda value: value)),
        'harbor.trial.trial': SimpleNamespace(Trial=Trial),
        'harbor.trial.hooks': SimpleNamespace(TrialEvent=SimpleNamespace(AGENT_START='start'))}
    original_import = builtins.__import__
    monkeypatch.setattr(builtins, '__import__', lambda name, *args, **kwargs: native[name] if name in native else original_import(name, *args, **kwargs))
    verdict = {'checks': {'delivery': True, 'financial_answer': True}}

    def verified(output, receipt, *args):
        receipt.update(status='verified', verdict=verdict)

    def rejected(*args):
        raise ValueError('credential_in_retained_artifact')

    monkeypatch.setattr(local_trial, 'record_verification', verified)
    monkeypatch.setattr(local_trial, 'retain_artifacts', rejected)
    args = guest_bench.trial_arguments(argparse.Namespace(dataset='workflow-v8', task='a01', attempt='retention-1'))
    with pytest.raises(ValueError, match='credential_in_retained_artifact'):
        asyncio.run(local_trial.run(args))
    receipt_path = tmp_path / '.raw/local-trials/retention-1/receipt.json'
    receipt = json.loads(receipt_path.read_text())
    assert receipt['status'] == 'infrastructure_failed'
    assert receipt['error_type'] == 'ValueError'
    assert receipt['verdict'] == verdict

    path, _ = configuration(tmp_path)
    monkeypatch.setattr(guest_bench, 'ROOT', tmp_path)
    monkeypatch.setattr(guest_bench, 'preflight', lambda: None)
    monkeypatch.setattr(guest_bench, 'load', lambda *args: {'tasks': {'a01': {'split': 'evaluation'}}})

    async def failed_run(args, credential=None):
        directory = tmp_path / '.raw/local-trials' / args.attempt
        directory.mkdir()
        (directory / 'receipt.json').write_text(json.dumps(receipt))
        raise ValueError('credential_in_retained_artifact')

    monkeypatch.setattr(guest_bench, 'run', failed_run)
    with pytest.raises(SystemExit, match='infrastructure failures'):
        guest_bench.batch(argparse.Namespace(dataset='workflow-v8', tasks=['a01'], split=None, profile=path, attempt='retention-batch'))
    summary = json.loads((tmp_path / '.raw/local-trials/retention-batch-batch.json').read_text())
    assert summary['status'] == 'infrastructure_failed'
