"""Thin local commands over llama.cpp and native Harbor verification."""
import argparse
import base64
import fcntl
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from workpaperbench.catalog import file_path, load
from fresh_replay import parse_json, read_bounded, reject_credential_patterns

GUEST = 'workpaperbench-local'
BUILDER = '/home/wpb/canonical-builder'
LIMA = Path.home() / '.local/opt/lima-2.2.0/bin/limactl'


def guest(*arguments, **kwargs):
    return subprocess.run([str(LIMA), 'shell', GUEST, *map(str, arguments)], check=True, **kwargs)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def configuration(path):
    raw = read_bounded(path, 20000)
    spec = parse_json(raw)
    if spec['execution_profile'] != 'local-lima' or spec['runtime']['backend'] != 'cpu':
        raise ValueError('unsupported_local_profile')
    return spec, hashlib.sha256(raw).hexdigest()


def request(port, route, timeout=10):
    with urllib.request.urlopen('http://127.0.0.1:' + str(port) + route, timeout=timeout) as response:
        return json.load(response)


def server_observations(path, start=0):
    return [parse_json(line) for line in read_bounded(path, 1000000).splitlines()[start:]]


def preflight():
    if platform.system() != 'Darwin' or platform.machine() != 'x86_64':
        raise ValueError('this_profile_requires_the_intel_mac')
    model = subprocess.check_output(['sysctl', '-n', 'hw.model'], text=True).strip()
    memory = int(subprocess.check_output(['sysctl', '-n', 'hw.memsize'], text=True))
    if model != 'MacPro7,1':
        raise ValueError('unexpected_execution_host')
    load(ROOT)
    print(json.dumps({'host_model': model, 'architecture': platform.machine(),
                      'memory_gib': memory / 1024**3,
                      'free_disk_gib': round(shutil.disk_usage(ROOT).free / 1024**3, 2),
                      'external_service_spend_usd': 0}, indent=2))
    guest('bash', '-lc', 'test -f /etc/workpaperbench-local-profile && test ! -d /Users && docker info >/dev/null && ~/runtime/bin/harbor --version')


def serve(path):
    spec, identity = configuration(path)
    weights = file_path(ROOT, spec['model']['weights'])
    runtime = file_path(ROOT, spec['runtime']['binary'])
    weights_hash, runtime_hash = digest(weights), digest(runtime)
    if weights_hash != spec['model']['sha256'] or runtime_hash != spec['runtime']['sha256']:
        raise ValueError('local_runtime_or_weights_changed')
    settings = spec['serving']
    command = [str(runtime), '--model', str(weights), '--alias', spec['model']['id'],
               '--host', '127.0.0.1', '--port', str(settings['port']),
               '--ctx-size', str(settings['context']), '--parallel', '1',
               '--threads', str(settings['threads']), '--threads-batch', str(settings['threads']),
               '--gpu-layers', '0', '--fit', 'off', '--jinja', '--reasoning', settings['reasoning'], '--metrics']
    if settings.get('rope_scaling'):
        command += ['--rope-scaling', settings['rope_scaling'], '--rope-scale', str(settings['rope_scale']),
                    '--yarn-orig-ctx', str(settings['yarn_original_context'])]
    if settings.get('flash_attention'):
        command += ['--flash-attn', settings['flash_attention'],
                    '--cache-type-k', settings['cache_type_k'], '--cache-type-v', settings['cache_type_v']]
    if settings.get('observe_slots'):
        command += ['--slots']
    if settings.get('context_shift') is False:
        command += ['--no-context-shift']
    generation = spec['candidate']['generation']
    command += ['--predict', str(generation['max_tokens'])]
    model_home = ROOT / '.local/model-home'
    model_home.mkdir(parents=True, exist_ok=True)
    environment = {'PATH': '/usr/bin:/bin', 'HOME': str(model_home), 'LANG': 'C.UTF-8'}
    policy = '(version 1)(allow default)(deny network-outbound)(allow network-outbound (remote ip "localhost:*"))'
    output = ROOT / '.raw/local-servers' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%f')
    output.mkdir(parents=True)
    with (output / 'server.log').open('w') as log:
        process = subprocess.Popen(['/usr/bin/sandbox-exec', '-p', policy, *command], env=environment, stdout=log, stderr=log)
        try:
            for _ in range(120):
                if process.poll() is not None:
                    raise ValueError('local_server_failed:' + str(output))
                try:
                    properties = request(settings['port'], '/props')
                    break
                except Exception:
                    time.sleep(1)
            else:
                raise ValueError('local_server_start_timeout')
            if properties['default_generation_settings']['n_ctx'] != settings['context']:
                raise ValueError('effective_context_changed')
            template_hash = hashlib.sha256(properties['chat_template'].encode()).hexdigest()
            if template_hash != spec['model']['chat_template_sha256']:
                raise ValueError('effective_chat_template_changed')
            record = {'profile_sha256': identity, 'profile': spec, 'pid': process.pid,
                      'weights_sha256': weights_hash, 'runtime_sha256': runtime_hash,
                      'chat_template_sha256': template_hash, 'command': command, 'settings_log': str(output / 'settings.jsonl'),
                      'network': 'Outbound connections denied except loopback',
                      'external_service_spend_usd': 0}
            (output / 'identity.json').write_text(json.dumps(record, indent=2) + '\n')
            (ROOT / '.local/active-server.json').write_text(json.dumps(record, indent=2) + '\n')
            print('Local server ready:', spec['model']['id'], 'profile', identity, flush=True)
            seen = set()
            with (output / 'settings.jsonl').open('x') as observations:
                while process.poll() is None:
                    if settings.get('observe_slots'):
                        for slot in request(settings['port'], '/slots', timeout=60):
                            if 'id_task' in slot and slot['id_task'] not in seen:
                                seen.add(slot['id_task'])
                                observations.write(json.dumps(slot) + '\n')
                                observations.flush()
                    time.sleep(2)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=20)


def prepare(dataset, tasks, profile=None, answer=None, artifacts=None, legacy=False):
    names = {'scripts/local_trial.py', 'scripts/fresh_replay.py', 'scripts/native_run.py',
             'scripts/fix_native_version.py', 'config/runtime.json', 'workpaperbench/__init__.py',
             'workpaperbench/catalog.py', 'workpaperbench/grading.py', 'workpaperbench/challenge_sql_worker.py',
             'datasets/' + dataset + '/manifest.json'}
    manifest = load(ROOT, dataset)
    names.update(manifest['hashes'])
    for key in tasks:
        _, _, task = load(ROOT, dataset, key)
        names.update(path.relative_to(ROOT).as_posix() for path in task.rglob('*') if path.is_file())
        if legacy:
            old = ROOT / 'datasets/challenge-v1/tasks' / key
            names.update(path.relative_to(ROOT).as_posix() for path in old.rglob('*')
                         if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc')
    if profile:
        installer = ROOT / '.local/runtime/hermes-agent/scripts/install.sh'
        names.add(installer.relative_to(ROOT).as_posix())
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w') as bundle:
        for name in sorted(names):
            path = file_path(ROOT, name)
            bundle.add(path, arcname=name, recursive=False)
        for name, data in (('.local/current-profile.json', read_bounded(profile, 20000) if profile else None),
                           ('.local/submitted-answer.json', answer)):
            if data is not None:
                member = tarfile.TarInfo(name)
                member.size = len(data)
                bundle.addfile(member, io.BytesIO(data))
        if artifacts:
            if artifacts.is_symlink() or len(list(artifacts.iterdir())) > 5:
                raise ValueError('unsafe_artifact_directory')
            for path in sorted(artifacts.iterdir()):
                if path.is_symlink() or not path.is_file() or (path.name != 'answer.json' and not re.fullmatch(r'[a-z][a-z0-9_]{0,40}\.sql', path.name)):
                    raise ValueError('unsafe_artifact_input')
                data = read_bounded(path, 65536 if path.name == 'answer.json' else 16384)
                reject_credential_patterns(data)
                member = tarfile.TarInfo('.local/submitted-artifacts/' + path.name)
                member.size = len(data)
                bundle.addfile(member, io.BytesIO(data))
        if profile:
            data = (ROOT / '.local/runtime/hermes-agent/scripts/install.sh').read_bytes()
            member = tarfile.TarInfo('.local/hermes-install.sh')
            member.size = len(data)
            bundle.addfile(member, io.BytesIO(data))
    guest('mkdir', '-p', BUILDER)
    guest('python3', '-c', "from pathlib import Path; import shutil; p=Path('/home/wpb/canonical-builder/.local/submitted-artifacts'); shutil.rmtree(p) if p.exists() else None")
    guest('tar', '-xf', '-', '-C', BUILDER, input=archive.getvalue())
    if profile:
        guest('/home/wpb/runtime/bin/python', '-c', "from importlib.metadata import distribution; from pathlib import Path; import hashlib; p=Path(distribution('harbor').locate_file('harbor/agents/installed/hermes.py')); raw=p.read_bytes(); assert hashlib.sha256(raw).hexdigest()=='012e980302b26641dcf77f31fe71a368b2022b098619853addd015c5e18e47c6', 'native_adapter_changed'; out=Path('/home/wpb/canonical-builder/.local/harbor-hermes-original.py'); out.parent.mkdir(exist_ok=True); out.write_bytes(raw)")


def collect(attempt):
    script = """import base64,json,pathlib,sys
r=pathlib.Path(sys.argv[1]); output={}
for name,limit in [('receipt.json',150000),('verifier.json',100000),('raw-answer.json',65536),('answer.json',65536)]:
 p=r/name
 if p.exists():
  if p.is_symlink() or not p.is_file() or p.stat().st_size>limit: raise ValueError('unsafe_receipt_file')
  output[name]=base64.b64encode(p.read_bytes()).decode()
for p in (r/'raw-sql').glob('*.sql'):
 if p.is_symlink() or not p.is_file() or p.stat().st_size>16384: raise ValueError('unsafe_sql_file')
 output['raw-sql/'+p.name]=base64.b64encode(p.read_bytes()).decode()
print(json.dumps(output))
"""
    response = guest('python3', '-c', script, BUILDER + '/.raw/local-trials/' + attempt, capture_output=True)
    files = parse_json(response.stdout)
    output = ROOT / '.raw/local-trials' / attempt
    output.mkdir(parents=True, exist_ok=False)
    for name, encoded in files.items():
        data = base64.b64decode(encoded, validate=True)
        reject_credential_patterns(data)
        target = file_path(output, name)
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
    return parse_json((output / 'receipt.json').read_bytes())


def execute(args):
    launcher_hash = digest(Path(__file__))
    manifest = load(ROOT, args.dataset)
    tasks = list(manifest['tasks']) if args.tasks == ['all'] else args.tasks or [args.task]
    if args.command == 'run' and args.dataset.startswith('workflow-'):
        if any(manifest['tasks'][key]['split'] != 'development' for key in tasks):
            raise ValueError('local_models_must_not_see_held_out_evaluation')
    answer = read_bounded(args.answer, 65536) if args.answer else None
    if answer is not None:
        reject_credential_patterns(answer)
    if args.command == 'replay':
        if args.legacy:
            from fresh_replay import discover_records, retained_input
            retained = []
            for stage in ('development','evaluation'):
                manifest = parse_json((ROOT / 'datasets/challenge-v1/manifests' / (stage+'.json')).read_bytes())
                from native_run import frozen_inputs
                frozen_inputs(manifest['manifest_id'], ROOT, reviewed_operations=True)
                for path, record, slot, audit in discover_records(ROOT,'challenge-v1',manifest):
                    if args.retained != 'all' and record['slot_id'] != args.retained:
                        continue
                    data, filename = retained_input(path / 'record.json' if path.name!='record.json' else path, record, audit)
                    if data is None:
                        raise ValueError('retained_original_artifact_unavailable')
                    retained.append((record['task'].removeprefix('challenge-v1-'), record['slot_id'],data))
            if not retained:
                raise ValueError('retained_legacy_slot_not_found')
            for key, slot_id, data in retained:
                submitted = ROOT / '.local' / ('replay-' + args.attempt + '-' + slot_id + '.json')
                submitted.parent.mkdir(exist_ok=True)
                submitted.write_bytes(data)
                replay_args = argparse.Namespace(**vars(args))
                replay_args.command = 'grade'
                replay_args.task = key
                replay_args.answer = submitted
                replay_args.attempt = args.attempt + '-' + slot_id
                execute(replay_args)
            return
        if args.retained == 'all':
            receipts = sorted((ROOT / '.raw/local-trials').glob('*/receipt.json'))
            selected = []
            for path in receipts:
                prior = parse_json(read_bounded(path,150000))
                if prior['manifest_id'] == manifest['manifest_id'] and (path.parent / 'raw-answer.json').is_file():
                    selected.append((path.parent.name, prior['task_id'].removeprefix(args.dataset+'-')))
            if not selected:
                raise ValueError('no_retained_artifacts_for_current_catalog')
            for name, key in selected:
                selected_args = argparse.Namespace(**vars(args))
                selected_args.retained = name
                selected_args.task = key
                selected_args.attempt = args.attempt + '-' + name
                execute(selected_args)
            return
        source = ROOT / '.raw/local-trials' / args.retained
        prior = parse_json(read_bounded(source / 'receipt.json', 150000))
        if prior['manifest_id'] != manifest['manifest_id'] or prior['task_id'] != args.dataset + '-' + tasks[0]:
            raise ValueError('retained_task_identity_mismatch')
        answer = read_bounded(source / 'raw-answer.json', 65536)
        if hashlib.sha256(answer).hexdigest() != prior['raw_answer_sha256']:
            raise ValueError('retained_answer_changed')
        if args.dataset.startswith('workflow-'):
            artifacts = ROOT / '.local' / ('replay-artifacts-' + args.attempt)
            artifacts.mkdir(parents=True,exist_ok=False)
            (artifacts / 'answer.json').write_bytes(answer)
            for name, expected in prior['sql_file_sha256'].items():
                raw = read_bounded(file_path(source / 'raw-sql',name),16384)
                if hashlib.sha256(raw).hexdigest() != expected:
                    raise ValueError('retained_sql_changed')
                (artifacts / name).write_bytes(raw)
            args.artifacts, answer = artifacts, None
    spec, profile_hash = configuration(args.profile) if args.command == 'run' else (None, None)
    transport = []
    listener_receipt = None
    if spec:
        active = parse_json(read_bounded(ROOT / '.local/active-server.json', 50000))
        if active['profile_sha256'] != profile_hash:
            raise ValueError('active_model_profile_mismatch')
        os.kill(active['pid'], 0)
        process_command = subprocess.check_output(['ps', '-p', str(active['pid']), '-o', 'command='], text=True)
        if str(file_path(ROOT, spec['runtime']['binary'])) not in process_command:
            raise ValueError('local_serving_process_changed')
        if request(spec['serving']['port'], '/v1/models')['data'][0]['id'] != spec['model']['id']:
            raise ValueError('local_serving_weights_identity_changed')
    attempts = [args.attempt if len(tasks) == args.repeat == 1 else f'{args.attempt}-{key}-{repeat}'
                for key in tasks for repeat in range(1, args.repeat + 1)]
    for attempt in attempts:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,80}', attempt):
            raise ValueError('derived_attempt_id_too_long')
        if (ROOT / '.raw/local-trials' / attempt).exists():
            raise ValueError('attempt_already_retained:' + attempt)
    guest('python3', '-c', "import pathlib,sys; base=pathlib.Path('/home/wpb/canonical-builder/.raw/local-trials'); assert not any((base/x).exists() for x in sys.argv[1:]), 'attempt_already_started'", *attempts)
    prepare(args.dataset, tasks, args.profile if spec else None, answer, args.artifacts, args.legacy)
    try:
        if spec:
            transport.append(subprocess.Popen(['ssh', '-F', str(Path.home() / '.lima' / GUEST / 'ssh.config'),
                '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '-o', 'ForwardAgent=no',
                '-o', 'ExitOnForwardFailure=yes', '-N', '-R',
                '127.0.0.1:18080:127.0.0.1:' + str(spec['serving']['port']), 'lima-' + GUEST]))
            time.sleep(1)
            if transport[0].poll() is not None:
                raise ValueError('local_model_transport_failed')
            listener_receipt = BUILDER + '/.local/transport-' + args.attempt + '.pid'
            transport.append(subprocess.Popen([str(LIMA), 'shell', GUEST, 'bash', '-c',
                'socat TCP-LISTEN:18080,bind=172.17.0.1,reuseaddr,fork TCP:127.0.0.1:18080 & pid=$!; echo "$pid" > "$1"; wait "$pid"',
                'local-listener', listener_receipt]))
            time.sleep(1)
            if transport[1].poll() is not None:
                raise ValueError('local_guest_listener_failed')
        for key in tasks:
            for repeat in range(1, args.repeat + 1):
                attempt = args.attempt if len(tasks) == args.repeat == 1 else f'{args.attempt}-{key}-{repeat}'
                command = [BUILDER + '/scripts/local_trial.py', '--dataset', args.dataset,
                           '--task', key, '--attempt', attempt]
                if answer is not None:
                    command += ['--answer', BUILDER + '/.local/submitted-answer.json']
                if args.artifacts:
                    command += ['--artifacts', BUILDER + '/.local/submitted-artifacts']
                if args.legacy:
                    command += ['--legacy']
                if spec:
                    command += ['--model', spec['model']['id'], '--configuration', BUILDER + '/.local/current-profile.json',
                                '--wall', str(spec['candidate']['wall_seconds']), '--turns', str(spec['candidate']['turns'])]
                before = len(server_observations(Path(active['settings_log']))) if spec else None
                try:
                    guest('/home/wpb/runtime/bin/python', *command, stdout=subprocess.DEVNULL)
                finally:
                    receipt = collect(attempt)
                    (ROOT / '.raw/local-trials' / attempt / 'launcher-observation.json').write_text(
                        json.dumps({'attempt_id':attempt,'launcher_sha256':launcher_hash}, indent=2) + '\n')
                    if spec:
                        observations = server_observations(Path(active['settings_log']), before)
                        for item in observations:
                            for setting, expected in spec['candidate']['generation'].items():
                                if abs(item['params'][setting] - expected) > 0.000001:
                                    raise ValueError('observed_generation_settings_differ:' + setting)
                        (ROOT / '.raw/local-trials' / attempt / 'server-observation.json').write_text(json.dumps({'attempt_id': attempt, 'profile_sha256': profile_hash, 'requests': observations}, indent=2) + '\n')
                    print('Receipt:', attempt, receipt['status'], receipt.get('verdict', {}).get('checks'))
    finally:
        try:
            if listener_receipt:
                guest('python3', '-c', "import os,pathlib,signal,sys; p=pathlib.Path(sys.argv[1]); pid=int(p.read_text()); proc=pathlib.Path('/proc')/str(pid)/'cmdline'; expected=[b'socat',b'TCP-LISTEN:18080,bind=172.17.0.1,reuseaddr,fork',b'TCP:127.0.0.1:18080']; alive=proc.exists(); assert not alive or proc.read_bytes().split(bytes([0]))[:3]==expected, 'listener_process_changed'; os.kill(pid,signal.SIGTERM) if alive else None; p.unlink()", listener_receipt)
        finally:
            for process in reversed(transport):
                process.terminate()
                process.wait(timeout=15)


def report(attempts, destination):
    rows = [parse_json(read_bounded(ROOT / '.raw/local-trials' / name / 'receipt.json', 150000)) for name in attempts]
    for name, row in zip(attempts, rows):
        directory = file_path(ROOT / '.raw/local-trials', name)
        if row['attempt_id'] != name:
            raise ValueError('report_attempt_identity_changed')
        for filename, field in (('verifier.json', 'verdict_sha256'), ('raw-answer.json', 'raw_answer_sha256'), ('answer.json', 'normalized_answer_sha256')):
            expected = row.get(field)
            if expected and digest(directory / filename) != expected:
                raise ValueError('report_retained_bytes_changed')
        for filename, expected in row.get('sql_file_sha256', {}).items():
            if digest(file_path(directory / 'raw-sql', filename)) != expected:
                raise ValueError('report_retained_sql_changed')
    identities = {(row['manifest_id'], row['scorer_sha256']) for row in rows}
    if len(identities) != 1:
        raise ValueError('report_task_or_scorer_versions_differ')
    configurations = {(row['inference'], row.get('model_configuration_sha256')) for row in rows}
    if len(configurations) != 1:
        raise ValueError('report_model_configurations_differ')
    if rows[0]['inference'] and not rows[0].get('model_configuration_sha256'):
        raise ValueError('report_model_configuration_unpinned')
    result = {'report_version': 'local-1.0', 'attempts': rows, 'external_service_spend_usd': 0,
              'held_out_evaluation': 'not run', 'frontier_discrimination': 'unmeasured'}
    with destination.open('x') as output:
        output.write(json.dumps(result, indent=2) + '\n')



def controls(attempt):
    prepare('workflow-v1', ['c01'])
    guest('docker', 'build', '-q', '-t', 'wpb-workflow-verifier-controls',
          BUILDER + '/datasets/workflow-v1/tasks/c01/tests', stdout=subprocess.DEVNULL)
    proof = guest('docker', 'run', '--rm', '--network', 'none', '--read-only',
                  '--memory', '384m', '--cpus', '1', '--pids-limit', '32',
                  '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '-i',
                  'wpb-workflow-verifier-controls', 'python', '-',
                  input=(ROOT / 'scripts/local_sql_controls.py').read_bytes(), capture_output=True)
    resource_checks = parse_json(proof.stdout)
    prepare('challenge-v2', ['c03'])
    guest('/home/wpb/runtime/bin/python', BUILDER + '/scripts/local_trial.py',
          '--dataset', 'challenge-v2', '--task', 'c03', '--attempt', attempt,
          '--boundaries', stdout=subprocess.DEVNULL)
    receipt = collect(attempt)
    if not all(receipt['candidate_boundary_checks'].values()):
        raise ValueError('candidate_boundary_control_failed')
    destination = ROOT / '.raw/local-trials' / attempt / 'resource-controls.json'
    destination.write_bytes(proof.stdout)
    print(json.dumps({'attempt_id': attempt, 'candidate': receipt['candidate_boundary_checks'],
                      'verifier': receipt['verdict']['isolation'], 'sql_resources': resource_checks}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('preflight')
    control_command = sub.add_parser('controls')
    control_command.add_argument('--attempt', required=True)
    serving = sub.add_parser('serve')
    serving.add_argument('--profile', type=Path, default=ROOT / 'config/local/qwen35-9b-terminal.json')
    for name in ('run', 'grade', 'replay'):
        command = sub.add_parser(name)
        command.add_argument('--dataset', default='challenge-v2')
        command.add_argument('--task', default='c03')
        command.add_argument('--tasks', nargs='+')
        command.add_argument('--attempt', required=True)
        command.add_argument('--repeat', type=int, default=1)
        command.add_argument('--legacy', action='store_true')
        artifact_input = command.add_mutually_exclusive_group(required=name == 'grade')
        artifact_input.add_argument('--answer', type=Path)
        artifact_input.add_argument('--artifacts', type=Path)
        command.add_argument('--profile', type=Path, default=ROOT / 'config/local/qwen35-9b-terminal.json')
        if name == 'replay':
            command.add_argument('--retained', required=True)
    reporting = sub.add_parser('report')
    reporting.add_argument('--attempts', nargs='+', required=True)
    reporting.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command in ('run', 'grade', 'replay', 'controls'):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,50}', args.attempt) or not 1 <= getattr(args, 'repeat', 1) <= 6:
            raise ValueError('invalid_local_attempt_or_repeat')
        if args.command == 'replay' and args.retained != 'all' and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,80}', args.retained):
            raise ValueError('invalid_retained_attempt')
        if args.command in ('grade', 'replay') and (args.repeat != 1 or args.tasks):
            raise ValueError('one_artifact_per_fresh_replay')
        (ROOT / '.local').mkdir(exist_ok=True)
        with (ROOT / '.local/local-command.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            controls(args.attempt) if args.command == 'controls' else execute(args)
    elif args.command == 'serve':
        serve(args.profile)
    elif args.command == 'report':
        if any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,80}', name) for name in args.attempts):
            raise ValueError('invalid_report_attempt')
        report(args.attempts, args.output)
    else:
        preflight()


if __name__ == '__main__':
    main()
