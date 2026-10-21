"""Run one native Harbor trial inside the dedicated local Linux guest."""
import argparse
import asyncio
import base64
from datetime import datetime, timezone
import hashlib
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import platform
import re
import shutil
import shlex
import socket
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from workpaperbench.catalog import load, tree_hash
from fresh_replay import ensure_no_symlink_ancestors, parse_json, read_bounded, reject_credential_patterns
from fix_native_version import corrected_hermes_source, ORIGINAL_MODULE_SHA256

HERMES_REVISION = '8b66a51036c1e20920a17cdd049fdf55c968d683'
INSTALLER_SHA256 = '25d3c95550e5ed7c0eec180a7d78dde765721c4e33639ab257c154c0a6e7554f'
DOCKER_CLIENT_ENV = {'DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_CONFIG', 'XDG_RUNTIME_DIR',
                     'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH', 'DOCKER_API_VERSION', 'DOCKER_DEFAULT_PLATFORM'}


class TrialBusyError(ValueError):
    """No attempt started because another process owns the native runtime."""


def endpoint_url(value):
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 for c in value):
        raise ValueError('invalid_model_endpoint')
    parsed = urlsplit(value)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment
            or '%' in parsed.hostname or not re.fullmatch(r'[A-Za-z0-9.:-]+', parsed.hostname)):
        raise ValueError('invalid_model_endpoint')
    port = parsed.port if parsed.port is not None else (443 if parsed.scheme == 'https' else 80)
    if not 1 <= port <= 65535:
        raise ValueError('invalid_model_endpoint_port')
    return parsed.hostname, port


def resolve_endpoint(value):
    hostname, port = endpoint_url(value)
    addresses = sorted({str(ipaddress.ip_address(row[4][0]))
                        for row in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)})
    if not addresses:
        raise ValueError('model_endpoint_unresolved')
    return {'hostname': hostname, 'port': port, 'addresses': addresses}


def endpoint_rules(endpoint):
    rules = ['add table inet workpaperbench_local',
             'add chain inet workpaperbench_local local_route { type route hook output priority -150; policy accept; }']
    destinations = [('ip6' if ipaddress.ip_address(address).version == 6 else 'ip') +
                    ' daddr ' + address + ' tcp dport ' + str(endpoint['port'])
                    for address in endpoint['addresses']]
    rules += ['add rule inet workpaperbench_local local_route ' + target + ' meta mark set 114514' for target in destinations]
    rules += ['add chain inet workpaperbench_local output { type filter hook output priority 10; policy drop; }',
              'add rule inet workpaperbench_local output ip daddr 127.0.0.11 counter drop']
    if any(ipaddress.ip_address(address).version == 6 for address in endpoint['addresses']):
        rules += ['add rule inet workpaperbench_local output ip6 hoplimit 255 icmpv6 type { nd-neighbor-solicit, nd-neighbor-advert } accept']
    rules += [
              'add rule inet workpaperbench_local output meta l4proto { icmp, ipv6-icmp } counter drop',
              'add rule inet workpaperbench_local output oifname "lo" accept']
    rules += ['add rule inet workpaperbench_local output ' + target + ' accept' for target in destinations]
    return '\n'.join([*rules, 'add rule inet workpaperbench_local output counter drop', ''])


def model_credential(configuration, supplied=None):
    name = configuration['serving'].get('api_key_env')
    if name is None:
        return 'local-only'
    value = supplied if supplied is not None else os.environ.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > 4096 or any(ord(c) < 33 for c in value):
        raise ValueError('model_api_key_missing_or_invalid')
    return value


def redact_secret(value, secret):
    if isinstance(value, str):
        return value.replace(secret, '[redacted]')
    if isinstance(value, dict):
        return {key: redact_secret(item, secret) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_secret(item, secret) for item in value]
    return value


def error_text(value, credential=None):
    text = str(value)
    return (text.replace(credential, '[redacted]') if credential else text)[:500]


def external_configuration(path):
    """Accept one explicit native route with credentials supplied separately."""
    raw = read_bounded(path, 20000)
    reject_credential_patterns(raw)
    spec = parse_json(raw)
    fields = {'configuration_id', 'execution_profile', 'model', 'runtime', 'serving',
              'candidate', 'harbor_version', 'hermes_revision'}
    if set(spec) != fields or spec['execution_profile'] != 'isolated-linux':
        raise ValueError('unsupported_external_profile')
    for key, required in (('model', {'id', 'revision'}), ('runtime', {'name', 'version'}),
                          ('candidate', {'wall_seconds', 'turns', 'generation', 'toolsets'})):
        if not isinstance(spec[key], dict) or set(spec[key]) != required:
            raise ValueError('external_configuration_fields:' + key)
    serving = spec['serving']
    if not isinstance(serving, dict) or not {'base_url', 'context'} <= set(serving) or set(serving) - {'base_url', 'context', 'api_key_env'}:
        raise ValueError('external_configuration_fields:serving')
    endpoint_url(serving['base_url'])
    if serving.get('api_key_env') is not None and (not isinstance(serving['api_key_env'], str)
            or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,99}', serving['api_key_env'])):
        raise ValueError('invalid_api_key_environment_name')
    strings = [spec['configuration_id'], *spec['model'].values(), *spec['runtime'].values()]
    if any(not isinstance(value, str) or not value.strip() or len(value) > 200
           or value.startswith('REPLACE_') for value in strings):
        raise ValueError('external_configuration_identity')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/:@-]{0,199}', spec['model']['id']):
        raise ValueError('external_model_id')
    if (spec['harbor_version'] != '0.23.0' or spec['hermes_revision'] != HERMES_REVISION
            or spec['candidate']['toolsets'] != 'terminal'):
        raise ValueError('external_native_route_or_version')
    candidate = spec['candidate']
    for value in (candidate['turns'], candidate['wall_seconds'], spec['serving']['context']):
        if type(value) is not int or value <= 0:
            raise ValueError('external_execution_budget')
    generation = candidate['generation']
    if (not isinstance(generation, dict) or 'max_tokens' not in generation
            or set(generation) - {'max_tokens', 'temperature', 'top_p', 'seed'}):
        raise ValueError('external_generation_fields')
    for name, low, high in (('max_tokens', 1, spec['serving']['context']),
                            ('temperature', 0, 2), ('top_p', 0.000001, 1), ('seed', 0, 2147483647)):
        if name not in generation:
            continue
        value = generation[name]
        if type(value) not in (int, float) or not low <= value <= high:
            raise ValueError('external_generation_budget:' + name)
        if name in ('max_tokens', 'seed') and type(value) is not int:
            raise ValueError('external_generation_integer:' + name)
    return spec, raw


RESUME_COMMAND = """export PATH="$HOME/.local/bin:$PATH" &&
mkdir -p /logs/artifacts &&
cp /opt/workpaperbench-runtime/resume-input/sql/*.sql /logs/artifacts/ &&
cat > /tmp/hermes/hermes-agent/_wpb_resume_import.py <<'WPB_RESUME'
import json
from pathlib import Path
from hermes_state import SessionDB

rows = [json.loads(line) for line in Path('/opt/workpaperbench-runtime/resume-input/session.jsonl').read_text().splitlines() if line.strip()]
db = SessionDB()
try:
    result = db.import_sessions(rows)
    assert result['ok'] and result['imported_ids'] == [rows[0]['id']], result
    saved = db.export_session(rows[0]['id'])
    assert len(saved['messages']) == len(rows[0]['messages'])
finally:
    db.close()
WPB_RESUME
hermes --run-module _wpb_resume_import
"""

def clean_environment(external=False):
    allowed = {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "PYTHONUNBUFFERED"}
    if external:
        allowed |= DOCKER_CLIENT_ENV
    for name in list(os.environ):
        if name not in allowed:
            del os.environ[name]
    if platform.system() != "Linux" or (not external and not Path("/etc/workpaperbench-local-profile").is_file()):
        raise ValueError("local_trial_requires_dedicated_guest")


def retain_artifacts(output, dataset, receipt, credential=None):
    artifact = output / 'trials' / receipt['attempt_id'] / 'artifacts/logs/artifacts/answer.json'
    if dataset.startswith('workflow-') and artifact.parent.exists():
        directory = ensure_no_symlink_ancestors(artifact.parent, ROOT)
        receipt['sql_file_sha256'] = {}
        raw_sql = output / 'raw-sql'
        raw_sql.mkdir()
        for path in sorted(directory.iterdir()):
            if path.name == 'answer.json':
                continue
            if not __import__('re').fullmatch(r'[a-z][a-z0-9_]{0,40}\.sql', path.name):
                raise ValueError('unsafe_retained_sql_name')
            path = ensure_no_symlink_ancestors(path, ROOT)
            data = read_bounded(path, 16384)
            reject_credential_patterns(data)
            if credential and credential.encode() in data:
                raise ValueError('credential_in_retained_artifact')
            (raw_sql / path.name).write_bytes(data)
            receipt['sql_file_sha256'][path.name] = hashlib.sha256(data).hexdigest()
    if not (artifact.exists() or artifact.is_symlink()):
        return
    artifact = ensure_no_symlink_ancestors(artifact, ROOT)
    answer = read_bounded(artifact, 65536)
    reject_credential_patterns(answer)
    if credential and credential.encode() in answer:
        raise ValueError('credential_in_retained_artifact')
    (output / 'raw-answer.json').write_bytes(answer)
    receipt['raw_answer_sha256'] = hashlib.sha256(answer).hexdigest()
    try:
        normalized = (json.dumps(parse_json(answer), indent=2, allow_nan=False) + '\n').encode()
        (output / 'answer.json').write_bytes(normalized)
        receipt['normalized_answer_sha256'] = hashlib.sha256(normalized).hexdigest()
    except ValueError:
        receipt['normalized_answer_sha256'] = None


def record_verification(output, receipt, exception_info=None, credential=None):
    """Retain the separate verdict even when the candidate exhausts its budget."""
    verifier = output / 'trials' / receipt['attempt_id'] / 'verifier/verdict.json'
    raw = read_bounded(verifier, 100000)
    if credential and credential.encode() in raw:
        raise ValueError('credential_in_verifier_artifact')
    verdict = parse_json(raw)
    isolation = verdict.get('isolation', {})
    required = {'network_probe_blocked', 'network_namespace_none',
                'no_inference_key', 'no_docker_socket'}
    if set(isolation) != required or not all(value is True for value in isolation.values()):
        raise ValueError('local_verifier_boundary_failed')
    (output / 'verifier.json').write_bytes(raw)
    receipt.update(verdict=verdict, verdict_sha256=hashlib.sha256(raw).hexdigest())
    if exception_info is None:
        receipt['status'] = 'verified'
    elif exception_info.exception_type in {'NonZeroAgentExitCodeError', 'AgentTimeoutError'}:
        receipt.update(status='candidate_failed',
                       candidate_error_type=exception_info.exception_type,
                       candidate_error=error_text(exception_info.exception_message, credential))
    else:
        raise RuntimeError(exception_info.exception_message)


def prepare_continuation(task, receipt, previous, configuration):
    """Copy only a matching candidate's native session and retained SQL."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,50}', previous):
        raise ValueError('invalid_continuation_attempt')
    directory = ensure_no_symlink_ancestors(ROOT / '.raw/local-trials' / previous, ROOT)
    raw = read_bounded(directory / 'receipt.json', 150000)
    prior = parse_json(raw)
    for key in ('task_id', 'task_sha256', 'manifest_id', 'scorer_sha256'):
        if prior[key] != receipt[key]:
            raise ValueError('continuation_task_changed')
    if not prior.get('inference'):
        raise ValueError('continuation_requires_candidate_history')
    prior_profile = prior['model_configuration']
    for key in ('model', 'runtime', 'serving', 'harbor_version', 'hermes_revision'):
        if prior_profile[key] != configuration[key]:
            raise ValueError('continuation_profile_changed:' + key)
    old_candidate, new_candidate = dict(prior_profile['candidate']), dict(configuration['candidate'])
    old_candidate.pop('turns')
    new_candidate.pop('turns')
    if old_candidate != new_candidate:
        raise ValueError('continuation_profile_changed:candidate')
    session_path = directory / 'trials' / previous / 'agent/hermes-session.jsonl'
    session = read_bounded(ensure_no_symlink_ancestors(session_path, ROOT), 2000000)
    reject_credential_patterns(session)
    rows = [parse_json(line) for line in session.splitlines() if line.strip()]
    if len(rows) != 1 or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', rows[0]['id']):
        raise ValueError('invalid_native_continuation_session')
    if rows[0].get('model') != configuration['model']['id']:
        raise ValueError('continuation_session_model_changed')
    target = task / 'environment/resume-input'
    target.mkdir()
    (target / 'session.jsonl').write_bytes(session)
    sql = target / 'sql'
    sql.mkdir()
    if not prior.get('sql_file_sha256'):
        raise ValueError('continuation_sql_missing')
    for filename, expected in prior['sql_file_sha256'].items():
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,40}\.sql', filename):
            raise ValueError('invalid_continuation_sql_name')
        path = ensure_no_symlink_ancestors(directory / 'raw-sql' / filename, ROOT)
        data = read_bounded(path, 16384)
        reject_credential_patterns(data)
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('continuation_sql_changed')
        (sql / filename).write_bytes(data)
    dockerfile = task / 'environment/Dockerfile'
    dockerfile.write_text(dockerfile.read_text() +
                         'COPY resume-input /opt/workpaperbench-runtime/resume-input\n')
    receipt['continuation'] = {
        'attempt_id': previous, 'receipt_sha256': hashlib.sha256(raw).hexdigest(),
        'session_id': rows[0]['id'], 'session_sha256': hashlib.sha256(session).hexdigest(),
        'sql_file_sha256': prior['sql_file_sha256'],
        'condition': 'Native session and saved SQL restored in a fresh isolated environment'}
    instruction = task / 'instruction.md'
    if instruction.exists():
        instruction.write_text(instruction.read_text() +
            '\nContinue the restored conversation and saved SQL in /logs/artifacts. '
            'Other temporary files may not persist. Complete and check the requested '
            'answer.json and SQL deliverables before ending.\n')
    return rows[0]['id']


def local_hermes_source(source, max_turns, generation=None, system_prompt="", external=False):
    corrected = corrected_hermes_source(source)
    installers = re.findall(rb'https://raw\.githubusercontent\.com/[^/\s]+/hermes-agent/main/scripts/install\.sh', corrected)
    if len(installers) != 1:
        raise ValueError('local_installer_revision_anchor')
    installer = installers[0]
    corrected = corrected.replace(b'curl -fsSL ' + installer + b' | bash -s --',
        b'bash /opt/workpaperbench-runtime/hermes-install.sh')
    install_environment = b'"set -euo pipefail; "\n'
    if corrected.count(install_environment) != 1:
        raise ValueError('local_install_environment_anchor')
    corrected = corrected.replace(install_environment,
        b'\'set -euo pipefail; export HERMES_HOME="/tmp/hermes" HERMES_INSTALL_DIR="/tmp/hermes/hermes-agent"; apt-get update && apt-get install -y sqlite3; \'\n')
    cli_anchor = b'            "hermes --yolo chat",\n'
    if corrected.count(cli_anchor) != 1:
        raise ValueError('local_cli_turn_limit_anchor')
    corrected = corrected.replace(cli_anchor,
        ('            "hermes --yolo chat --max-turns ' + str(max_turns) + '",\n').encode())
    corrected = corrected.replace(b'--skip-setup{branch_flag}', b'--skip-setup --skip-browser --skip-computer-use{branch_flag}')
    warmup = b'                "hermes --version"\n'
    if corrected.count(warmup) != 1:
        raise ValueError('local_cli_warmup_anchor')
    corrected = corrected.replace(warmup, b'                "hermes --version && hermes chat --help && hermes pm env npm"\n')
    before = b'_NATIVE_PROVIDERS: dict[str, tuple[str | None, list[str]]] = {\n'
    if corrected.count(before) != 1:
        raise ValueError("local_native_provider_anchor")
    corrected = corrected.replace(before, before + b'    "custom": ("custom", ["OPENAI_API_KEY"]),\n')
    corrected = corrected.replace(b'if use_native and provider == "openai":', b'if use_native and provider in ("openai", "custom"):')
    before = b'        config_yaml = self._build_config_yaml(cli_model)\n'
    generation = generation or {'max_tokens': 2048, 'temperature': 0.6, 'top_p': 0.95, 'top_k': 20, 'seed': 17}
    block = '''        if provider != "custom" or env.get("OPENAI_API_KEY") != "local-only":
            raise ValueError("Local profile requires its credential-free custom route")
        if env.get("OPENAI_BASE_URL") != "http://172.17.0.1:18080/v1":
            raise ValueError("Unexpected local model endpoint")
        local_config = yaml.safe_load(self._build_config_yaml(cli_model))
        route = {"default": model, "provider": "custom", "base_url": env["OPENAI_BASE_URL"],
                 "api_key": "local-only", "api_mode": "chat_completions"}
        local_config["model"] = route
        local_config["custom_providers"] = [{"name": "workpaperbench-local", "base_url": env["OPENAI_BASE_URL"],
            "api_key": "local-only", "model": model, "context_length": CONTEXT_LENGTH, "extra_body": GENERATION}]
        local_config["provider"] = "custom"
        local_config["fallback_model"] = None
        local_config["agent"]["max_turns"] = MAX_TURNS
        local_config["agent"]["system_prompt"] = SYSTEM_PROMPT
        local_config["compression"]["enabled"] = False
        local_config["auxiliary"] = {"title_generation": {"enabled": False, "model_upgrade_enabled": False}}
        for role in ("vision", "compression", "approval", "review", "skills_hub", "mcp"):
            local_config["auxiliary"][role] = {"provider": "custom", "model": model,
                "base_url": env["OPENAI_BASE_URL"], "api_key": "local-only", "api_mode": "chat_completions"}
        config_yaml = yaml.dump(local_config, default_flow_style=False)
'''.replace("MAX_TURNS", str(max_turns)).replace('SYSTEM_PROMPT', repr(system_prompt)).replace('CONTEXT_LENGTH', str(generation.pop('_context', 16384))).replace('GENERATION', repr(generation)).encode()
    if corrected.count(before) != 1:
        raise ValueError("local_native_config_anchor")
    if external:
        block = block.replace(b'env.get("OPENAI_API_KEY") != "local-only"', b'not env.get("OPENAI_API_KEY")')
        block = block.replace(b'env.get("OPENAI_BASE_URL") != "http://172.17.0.1:18080/v1"', b'not env.get("OPENAI_BASE_URL")')
        block = block.replace(b'"api_key": "local-only"', b'"key_env": "OPENAI_API_KEY"')
    return corrected.replace(before, block)


async def run(arguments, credential=None):
    external = getattr(arguments, 'execution_profile', None) == 'isolated-linux'
    secret = None
    if arguments.configuration:
        declared = parse_json(read_bounded(arguments.configuration, 20000))
        external = declared.get('execution_profile') == 'isolated-linux'
        if external:
            declared, _ = external_configuration(arguments.configuration)
            credential = model_credential(declared, credential)
            secret = credential if declared['serving'].get('api_key_env') else None
            if secret and secret.encode() in read_bounded(arguments.configuration, 20000):
                raise ValueError('credential_in_model_profile')
    clean_environment(external=external)
    (ROOT / '.local').mkdir(exist_ok=True)
    trial_lock = (ROOT / '.local/local-trial.lock').open('a')
    try:
        fcntl.flock(trial_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        raise TrialBusyError('another_local_trial_is_running') from error
    manifest, spec, source = load(ROOT, arguments.dataset, arguments.task)
    configuration = None
    if arguments.configuration:
        config_bytes = read_bounded(arguments.configuration, 20000)
        configuration = parse_json(config_bytes)
        if configuration.get('execution_profile') == 'isolated-linux':
            configuration, config_bytes = external_configuration(arguments.configuration)
        if (configuration['model']['id'] != arguments.model
                or configuration['execution_profile'] not in ('local-lima', 'isolated-linux')
                or configuration['candidate']['turns'] != arguments.turns
                or configuration['candidate']['wall_seconds'] != arguments.wall):
            raise ValueError('effective_model_configuration_mismatch')
    if arguments.model and not external and arguments.dataset.startswith('workflow-') and spec.get('split') != 'development':
        raise ValueError('local_models_must_not_see_held_out_evaluation')
    smoke = getattr(arguments, 'transport_smoke', False)
    if smoke and (not configuration or configuration['model']['id'] != 'deterministic-harness-fixture'):
        raise ValueError('transport_smoke_requires_scripted_fixture')
    output = ROOT / ".raw/local-trials" / arguments.attempt
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    receipt = {"attempt_id": arguments.attempt, "execution_profile": configuration['execution_profile'] if configuration else getattr(arguments, 'execution_profile', 'local-lima'),
               "manifest_id": manifest["manifest_id"], "task_id": spec["task_id"],
               "task_sha256": spec["task_sha256"], "scorer_version": manifest["scorer_version"],
               "scorer_sha256": manifest["scorer_sha256"], "started_at": started,
               "external_service_spend_usd": 0, "status": "started", "inference": arguments.model is not None and not smoke}
    if receipt['execution_profile'] == 'isolated-linux':
        receipt['source_kind'] = 'scripted_harness_fixture' if smoke else ('model_evaluation' if arguments.model else 'submitted_artifact_replay')
        receipt['configuration_evidence'] = 'Declared model revision, serving runtime, model ID and generation settings. Native version is checked. Server identity and enforcement are not independently observed.'
        receipt['external_service_spend_usd'] = None if arguments.model and not smoke else 0
        receipt['evaluation_track'] = manifest.get('evaluation_track', 'maintenance')
        receipt['task_split'] = spec.get('split')
        contract = source / 'environment/output_contract.json'
        receipt['requested_tables'] = list(parse_json(read_bounded(contract, 100000))['tables']) if contract.is_file() else []
    receipt['execution_files_sha256'] = {name:hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in ('scripts/local_trial.py','scripts/fresh_replay.py','scripts/fix_native_version.py','scripts/native_run.py','config/runtime.json')}
    if configuration:
        receipt['model_configuration'] = configuration
        receipt['model_configuration_sha256'] = hashlib.sha256(config_bytes).hexdigest()
    (output / "start.json").write_text(json.dumps(receipt, indent=2) + "\n")
    try:
        endpoint = resolve_endpoint(configuration['serving']['base_url']) if external and arguments.model else {
            'hostname': '172.17.0.1', 'port': 18080, 'addresses': ['172.17.0.1']}
        if external:
            receipt['model_endpoint'] = endpoint if arguments.model else None
        task = output / "task"
        # Fresh file metadata avoids reusing a context checksum for equal-sized
        # SQLite files retained with the same original archive timestamps.
        shutil.copytree(source, task, copy_function=shutil.copy)
        if external and arguments.model:
            toml = task / 'task.toml'
            toml.write_text(re.sub(r'(?m)^allowed_hosts = .*$',
                                  'allowed_hosts = ' + json.dumps([endpoint['hostname']]), toml.read_text()))
        if arguments.legacy:
            if arguments.model or arguments.dataset != 'challenge-v2':
                raise ValueError('legacy_replay_is_inference_free')
            canonical_gold = parse_json((task / 'tests/gold.json').read_bytes())
            shutil.rmtree(task)
            legacy_source = ROOT / 'datasets/challenge-v1/tasks' / arguments.task
            shutil.copytree(legacy_source, task, copy_function=shutil.copy,
                            ignore=shutil.ignore_patterns('__pycache__','*.pyc','._*'))
            if tree_hash(task) != spec['origin_task_sha256']:
                raise ValueError('legacy_source_dossier_changed')
            gold = parse_json((task / 'tests/gold.json').read_bytes())
            for identifier, declaration in gold['answers'].items():
                declaration['evidence'] = canonical_gold['answers'][identifier]['evidence']
            if gold.get('conclusion') is not None:
                gold['conclusion']['evidence'] = canonical_gold['conclusion']['evidence']
            gold['scorer_version'] = manifest['scorer_version']
            shutil.copyfile(source / 'tests/workpaperbench/challenge_grading.py', task / 'tests/workpaperbench/challenge_grading.py')
            shutil.copyfile(source / 'tests/verify.py', task / 'tests/verify.py')
            gold['hashes']['verify.py'] = hashlib.sha256((task / 'tests/verify.py').read_bytes()).hexdigest()
            (task / 'tests/gold.json').write_text(json.dumps(gold,indent=2) + '\n')
            toml = task / 'task.toml'
            toml.write_text(toml.read_text().replace('allowed_hosts = ["openrouter.ai"]', 'allowed_hosts = ["172.17.0.1"]'))
            receipt.update(task_id=gold['task_id'], source_task_sha256=spec['origin_task_sha256'],
                           source_snapshot='challenge-v1 original published candidate dossier',
                           historical_inputs_repaired=False)
        if arguments.model:
            installer_path = ROOT / '.local/hermes-install.sh'
            installer_bytes = read_bounded(installer_path, 100000)
            receipt['hermes_installer_sha256'] = hashlib.sha256(installer_bytes).hexdigest()
            if receipt['execution_profile'] == 'isolated-linux' and receipt['hermes_installer_sha256'] != INSTALLER_SHA256:
                raise ValueError('external_pinned_installer_changed')
            (task / 'environment/hermes-install.sh').write_bytes(installer_bytes)
            dockerfile = task / 'environment/Dockerfile'
            dockerfile.write_text(dockerfile.read_text() + 'COPY hermes-install.sh /opt/workpaperbench-runtime/hermes-install.sh\n')
        if arguments.answer:
            answer = read_bounded(arguments.answer, 65536)
            reject_credential_patterns(answer)
            encoded = base64.b64encode(answer).decode()
            (task / "solution/solve.sh").write_text(
                "#!/bin/bash\nset -euo pipefail\npython - <<'WRITE'\n"
                "import base64\nfrom pathlib import Path\n"
                "Path('/logs/artifacts/answer.json').write_bytes(base64.b64decode(" + repr(encoded) + "))\nWRITE\n")
        if arguments.artifacts:
            directory = arguments.artifacts
            if directory.is_symlink() or not directory.is_dir() or len(list(directory.iterdir())) > 5:
                raise ValueError('unsafe_submission_directory')
            script = "#!/bin/bash\nset -euo pipefail\npython - <<'WRITE'\nimport base64\nfrom pathlib import Path\n"
            for path in sorted(directory.iterdir()):
                if path.name != 'answer.json' and not __import__('re').fullmatch(r'[a-z][a-z0-9_]{0,40}\.sql', path.name):
                    raise ValueError('unsafe_submission_name')
                raw = read_bounded(path, 65536 if path.name == 'answer.json' else 16384)
                reject_credential_patterns(raw)
                script += "Path('/logs/artifacts/" + path.name + "').write_bytes(base64.b64decode(" + repr(base64.b64encode(raw).decode()) + "))\n"
            (task / 'solution/solve.sh').write_text(script + 'WRITE\n')
        if arguments.boundaries:
            original_solution = (task / "solution/solve.sh").read_text()
            probe = '''python - <<'BOUNDARIES'
import json, socket
from pathlib import Path
checks = {}
for name in ('/tests/gold.json', '/workspace/.git', '/Users', '/root/.ssh', '/var/run/docker.sock'):
    checks['unavailable:' + name] = not Path(name).exists()
checks['fresh_candidate_state'] = not Path('/workspace/local-state-probe').exists()
Path('/workspace/local-state-probe').write_text('one trial only')
for host, port, label in [('1.1.1.1',443,'external_tls'), ('172.17.0.1',22,'guest_ssh'), ('172.17.0.1',2375,'daemon_tcp')]:
    try:
        with socket.create_connection((host, port),timeout=2): pass
        checks[label + '_blocked'] = False
    except OSError:
        checks[label + '_blocked'] = True
for host, port, label in [('1.1.1.1',53,'external_dns_udp'),('127.0.0.11',53,'docker_dns_stub')]:
    probe=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    probe.settimeout(2)
    try:
        probe.sendto(bytes.fromhex('aabb01000001000000000000076578616d706c6503636f6d0000010001'),(host,port))
        probe.recvfrom(512)
        checks[label+'_blocked']=False
    except OSError:
        checks[label+'_blocked']=True
    finally:
        probe.close()
checks['icmp_probe_available'] = False
try:
    probe=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_ICMP)
    checks['icmp_probe_available'] = True
    probe.settimeout(2)
    probe.sendto(bytes.fromhex('0800f7fd00010001'),('1.1.1.1',0))
    probe.recvfrom(512)
    checks['external_icmp_blocked'] = False
except OSError:
    checks['external_icmp_blocked'] = True
finally:
    if checks['icmp_probe_available']: probe.close()
Path('/workspace/data.sqlite').write_bytes(b'candidate overwrite must not reach pristine verification')
Path('/workspace/local-boundaries.json').write_text(json.dumps(checks))
assert all(checks.values()), checks
BOUNDARIES
'''
            (task / "solution/solve.sh").write_text(original_solution.replace('set -euo pipefail\n', 'set -euo pipefail\n' + probe, 1))
        continuation_id = None
        if getattr(arguments, 'continue_from', None):
            if not configuration or spec.get('split') != 'development':
                raise ValueError('continuation_requires_development_inference')
            continuation_id = prepare_continuation(task, receipt, arguments.continue_from, configuration)
        receipt['effective_task_sha256'] = tree_hash(task)
        from harbor.models.trial.config import TrialConfig
        from harbor.trial.trial import Trial
        from harbor.trial.hooks import TrialEvent
        agent = {"name": "oracle", "override_timeout_sec": 120}
        if arguments.model:
            from importlib.metadata import distribution
            distribution_path = distribution("harbor").locate_file("harbor/agents/installed/hermes.py")
            adapter = Path(distribution_path)
            original = adapter.read_bytes()
            if receipt['execution_profile'] == 'isolated-linux':
                if distribution('harbor').version != '0.23.0' or hashlib.sha256(original).hexdigest() != ORIGINAL_MODULE_SHA256:
                    raise ValueError('external_native_adapter_changed')
            elif original != (ROOT / ".local/harbor-hermes-original.py").read_bytes():
                raise ValueError("local_native_adapter_changed")
            generation = copy_generation = dict(configuration['candidate']['generation']) if configuration else None
            if copy_generation is not None:
                copy_generation['_context'] = configuration['serving']['context']
            effective = local_hermes_source(original, arguments.turns, generation, configuration["candidate"].get("system_prompt", "") if configuration else "", external=external)
            adapter.write_bytes(effective)
            receipt["native_adapter_sha256"] = hashlib.sha256(effective).hexdigest()
            os.environ["OPENAI_API_KEY"] = credential if external else "local-only"
            os.environ["OPENAI_BASE_URL"] = configuration['serving']['base_url'] if external else "http://172.17.0.1:18080/v1"
            agent = {"name": "hermes", "model_name": "custom/" + arguments.model,
                     "override_timeout_sec": arguments.wall, "override_setup_timeout_sec": 1200,
                     "kwargs": {"version": "v0.21.4+canary.20261004T084456Z", "toolsets": configuration["candidate"].get("toolsets", "file,terminal,skills") if configuration else "file,terminal,skills"}}
        config = TrialConfig.model_validate({"task": {"path": str(task)}, "trial_name": arguments.attempt,
                                           "trials_dir": str(output / "trials"), "agent": agent,
                                           "environment": {"type": "docker"}})
        trial = await Trial.create(config)
        async def enforce_local_network(event):
            command = ['docker', 'ps', '--filter', 'label=com.docker.compose.project=' + arguments.attempt + '__env',
                       '--filter', 'label=com.docker.compose.service=harbor-docker-egress-control-sidecar',
                       '--format', '{{.ID}}']
            sidecar = subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
            if not __import__('re').fullmatch(r'[0-9a-f]{12,64}', sidecar):
                raise ValueError('local_egress_sidecar_missing')
            rules = endpoint_rules(endpoint)
            subprocess.run(['docker', 'exec', '-i', sidecar, 'nft', '-f', '-'], input=rules,
                           capture_output=True, text=True, timeout=10, check=True)
            receipt['candidate_network_policy'] = ('Loopback and declared endpoint IP addresses/TCP port only. IPv6 endpoints additionally allow neighbor solicitation/advertisement with hop limit 255. Other ICMP, DNS and nonendpoint traffic are dropped.' if external else 'Loopback and guest bridge TCP 18080 only, all other IPv4/IPv6 protocols dropped')
            if external and arguments.model:
                hosts = '\n'.join(address + ' ' + endpoint['hostname'] for address in endpoint['addresses'])
                pinned = await trial.agent_environment.exec(
                    command="printf '%s\\n' " + shlex.quote(hosts) + ' >> /etc/hosts', timeout_sec=10)
                if pinned.return_code:
                    raise ValueError('candidate_endpoint_resolution_not_pinned')
                receipt['candidate_endpoint_resolution_pinned'] = True
            if arguments.model and not external:
                health = await trial.agent_environment.exec(
                    command='curl --fail --silent --connect-timeout 5 --max-time 10 http://172.17.0.1:18080/v1/models', timeout_sec=12)
                if health.return_code:
                    raise ValueError('candidate_local_model_route_unavailable')
                models = parse_json(health.stdout)
                if arguments.model not in [item['id'] for item in models['data']]:
                    raise ValueError('candidate_local_model_identity_changed')
                receipt['candidate_local_model_health'] = True
        trial.add_hook(TrialEvent.AGENT_START, enforce_local_network)
        if arguments.boundaries:
            async def retain_boundaries(event):
                probe = await trial.agent_environment.exec(command="cat /workspace/local-boundaries.json", timeout_sec=10)
                receipt['candidate_boundary_checks'] = parse_json(probe.stdout)
            trial.add_hook(TrialEvent.AGENT_END, retain_boundaries)
        if arguments.model:
            async def check_version(event):
                result = await trial.agent_environment.exec(
                    command="git -C /tmp/hermes/hermes-agent rev-parse HEAD", timeout_sec=10)
                if result.return_code or result.stdout.strip() != "8b66a51036c1e20920a17cdd049fdf55c968d683":
                    raise ValueError("local_hermes_revision_mismatch")
            trial.add_hook(TrialEvent.AGENT_START, check_version)
            if continuation_id:
                async def restore_candidate(event):
                    await trial.agent.exec_as_agent(
                        trial.agent_environment,
                        command=RESUME_COMMAND,
                        env={'HERMES_HOME': '/tmp/hermes'}, timeout_sec=60)
                    trial.agent._resume = True
                    trial.agent._native_session_id = continuation_id
                    receipt['native_session_restored'] = True
                    (output / 'continuation-ready.json').write_text(
                        json.dumps(receipt['continuation'], indent=2) + '\n')
                trial.add_hook(TrialEvent.AGENT_START, restore_candidate)
        result = await trial.run()
        if continuation_id and not receipt.get('native_session_restored'):
            raise RuntimeError('native_continuation_not_restored')
        record_verification(output, receipt, result.exception_info, secret)
    except asyncio.CancelledError:
        receipt.update(status='cancelled', error='Local trial cancelled before a completed verifier receipt')
        raise
    except Exception as error:
        receipt.update(status="infrastructure_failed", error=error_text(error, secret), error_type=type(error).__name__)
        raise
    finally:
        try:
            retain_artifacts(output, arguments.dataset, receipt, secret)
        except Exception as error:
            receipt["retention_error"] = error_text(error, secret)
            receipt.update(status='infrastructure_failed', error_type=type(error).__name__,
                           error='artifact_retention_failed:' + error_text(error, secret))
            raise
        finally:
            if arguments.model and 'original' in locals():
                adapter.write_bytes(original)
            native_result = output / 'trials' / arguments.attempt / 'result.json'
            if native_result.is_file():
                from workpaperbench.execution_report import trial_metrics
                try:
                    receipt['execution_metrics'] = trial_metrics(native_result)
                except (OSError, ValueError, TypeError):
                    receipt['execution_metrics'] = None
            receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
            if secret:
                receipt = redact_secret(receipt, secret)
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("OPENAI_BASE_URL", None)
            (output / "receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="challenge-v2")
    parser.add_argument("--task", default="c03")
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--answer", type=Path)
    parser.add_argument('--artifacts', type=Path)
    parser.add_argument('--legacy', action='store_true')
    parser.add_argument("--continue-from")
    parser.add_argument("--model")
    parser.add_argument('--configuration', type=Path)
    parser.add_argument('--transport-smoke', action='store_true')
    parser.add_argument("--boundaries", action="store_true")
    parser.add_argument("--wall", type=int, default=600)
    parser.add_argument("--turns", type=int, default=12)
    args = parser.parse_args()
    if not __import__('re').fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}", args.attempt):
        raise SystemExit("Invalid attempt ID")
    asyncio.run(run(args))
