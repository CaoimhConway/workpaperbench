"""Run the existing native harness directly in a dedicated Linux guest."""
import argparse
import asyncio
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from local_trial import external_configuration, model_credential, run
from local_bench import report
from workpaperbench.catalog import load


def preflight():
    if platform.system() != 'Linux':
        raise ValueError('external_profile_requires_linux_docker')
    from importlib.metadata import distribution
    import hashlib
    from local_trial import ORIGINAL_MODULE_SHA256
    package = distribution('harbor')
    if package.version != '0.23.0':
        raise ValueError('external_harbor_version')
    adapter = Path(package.locate_file('harbor/agents/installed/hermes.py'))
    if hashlib.sha256(adapter.read_bytes()).hexdigest() != ORIGINAL_MODULE_SHA256:
        raise ValueError('external_native_adapter_changed')
    subprocess.run(['docker', 'info'], check=True, stdout=subprocess.DEVNULL, timeout=30)
    print('Linux Docker runtime and pinned Harbor 0.23.0 adapter verified.')


def selected_tasks(dataset, tasks=None, split='all'):
    manifest = load(ROOT, dataset)
    selected = tasks if tasks is not None else [key for key, spec in manifest['tasks'].items()
                                               if split == 'all' or spec.get('split') == split]
    if not selected or len(set(selected)) != len(selected) or any(key not in manifest['tasks'] for key in selected):
        raise ValueError('invalid_task_selection')
    return selected


def batch(args):
    selected = selected_tasks(args.dataset, args.tasks, args.split or 'all')
    configurations, _ = external_configuration(args.profile)
    credential = model_credential(configurations)
    trials = [trial_arguments(argparse.Namespace(**{**vars(args), 'task': task,
                               'attempt': args.attempt + '-' + task}), args.profile) for task in selected]
    output = ROOT / '.raw/local-trials'
    summary = output / (args.attempt + '-batch.json')
    if summary.exists() or any((output / trial.attempt).exists() for trial in trials):
        raise ValueError('attempt_already_exists')
    preflight()
    output.mkdir(parents=True, exist_ok=True)
    with summary.open('x') as stream:
        stream.write(json.dumps({'status': 'started', 'attempts': []}) + '\n')
    outcomes = []
    for trial in trials:
        try:
            asyncio.run(run(trial, credential=credential))
        except Exception:
            receipt = output / trial.attempt / 'receipt.json'
            if not receipt.is_file():
                summary.write_text(json.dumps({'status': 'infrastructure_failed',
                    'failed_to_start': trial.attempt, 'attempts': outcomes}, indent=2) + '\n')
                raise
        row = json.loads((output / trial.attempt / 'receipt.json').read_text())
        outcomes.append({'attempt_id': trial.attempt, 'task_id': row['task_id'], 'status': row['status']})
        summary.write_text(json.dumps({'status': 'running', 'attempts': outcomes}, indent=2) + '\n')
    failed = any(row['status'] not in ('verified', 'candidate_failed') for row in outcomes)
    summary.write_text(json.dumps({'status': 'infrastructure_failed' if failed else 'completed',
                                  'attempts': outcomes}, indent=2) + '\n')
    if failed:
        raise SystemExit('Batch retained infrastructure failures. Inspect individual receipts.')


def trial_arguments(args, profile=None, smoke=False):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,50}', args.attempt):
        raise ValueError('invalid_attempt_id')
    values = {'dataset': args.dataset, 'task': args.task, 'attempt': args.attempt,
              'answer': None, 'artifacts': getattr(args, 'artifacts', None),
              'legacy': False, 'continue_from': None, 'boundaries': False,
              'model': None, 'configuration': None, 'wall': 600, 'turns': 12,
              'execution_profile': 'isolated-linux', 'transport_smoke': smoke}
    if profile:
        spec, _ = external_configuration(profile)
        values.update(model=spec['model']['id'], configuration=profile,
                      wall=spec['candidate']['wall_seconds'], turns=spec['candidate']['turns'])
    return argparse.Namespace(**values)


class FixtureHandler(BaseHTTPRequestHandler):
    """A scripted protocol fixture. It makes no inference and reads no answers."""
    def __init__(self, *args, observations, credential='local-only', **kwargs):
        self.observations = observations
        self.credential = credential
        super().__init__(*args, **kwargs)

    def log_message(self, *args):
        pass

    def send(self, payload, content_type='application/json'):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != '/v1/models':
            self.send_error(404)
            return
        self.send({'object': 'list', 'data': [{'id': 'deterministic-harness-fixture', 'object': 'model'}]})

    def do_POST(self):
        if self.headers.get('Authorization') != 'Bearer ' + self.credential:
            self.send_error(401)
            return
        length = int(self.headers.get('Content-Length', '0'))
        if self.path != '/v1/chat/completions' or not 0 < length <= 2000000 or len(self.observations) >= 6:
            self.send_error(400)
            return
        request = json.loads(self.rfile.read(length))
        tools = [item['function']['name'] for item in request.get('tools', [])]
        returned = any(item.get('role') == 'tool' and item.get('tool_call_id') == 'wpb-fixture-call'
                       and 'WPB_TRANSPORT_OK' in str(item.get('content')) for item in request['messages'])
        if request.get('model') != 'deterministic-harness-fixture' or ('terminal' not in tools and not returned):
            self.send_error(400)
            return
        self.observations.append({'model': request['model'], 'tool_result_observed': returned,
                                  'generation': {name: request.get(name) for name in ('max_tokens', 'temperature', 'top_p', 'seed')}})
        message = {'role': 'assistant', 'content': 'Scripted transport fixture complete.' if returned else None}
        if not returned:
            command = "mkdir -p /logs/artifacts && printf '{}' > /logs/artifacts/answer.json && printf 'WPB_TRANSPORT_OK\\n'"
            message['tool_calls'] = [{'id': 'wpb-fixture-call', 'type': 'function',
                                     'function': {'name': 'terminal', 'arguments': json.dumps({'command': command})}}]
        finish = 'stop' if returned else 'tool_calls'
        base = {'id': 'wpb-scripted-response', 'created': 0, 'model': request['model']}
        if request.get('stream'):
            delta = dict(message)
            if 'tool_calls' in delta:
                delta['tool_calls'] = [{'index': 0, **delta['tool_calls'][0]}]
            chunks = [{**base, 'object': 'chat.completion.chunk',
                       'choices': [{'index': 0, 'delta': delta, 'finish_reason': None}]},
                      {**base, 'object': 'chat.completion.chunk',
                       'choices': [{'index': 0, 'delta': {}, 'finish_reason': finish}]}]
            wire = ''.join('data: ' + json.dumps(chunk) + '\n\n' for chunk in chunks) + 'data: [DONE]\n\n'
            self.send(wire.encode(), 'text/event-stream')
        else:
            self.send({**base, 'object': 'chat.completion',
                       'choices': [{'index': 0, 'message': message, 'finish_reason': finish}],
                       'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}})


def smoke(args):
    preflight()
    spec = json.loads((ROOT / 'config/external-model.example.json').read_text())
    spec.update(configuration_id='deterministic-native-transport-1',
                model={'id': 'deterministic-harness-fixture', 'revision': 'scripted-no-inference'},
                runtime={'name': 'Python standard-library protocol fixture', 'version': '1'})
    spec['candidate'].update(turns=3, wall_seconds=180)
    host = args.host
    if host is None:
        bridge = json.loads(subprocess.check_output(['docker', 'network', 'inspect', 'bridge'], text=True, timeout=30))
        host = bridge[0]['IPAM']['Config'][0]['Gateway']
    spec['serving']['base_url'] = 'http://' + host + ':' + str(args.port) + '/v1'
    credential = 'fixture-only-no-provider-credential' if args.authenticated else 'local-only'
    spec['serving'].pop('api_key_env', None)
    if args.authenticated:
        spec['serving']['api_key_env'] = 'WPB_FIXTURE_API_KEY'
    directory = ROOT / '.local'
    directory.mkdir(exist_ok=True)
    profile = directory / (args.attempt + '-transport-profile.json')
    with profile.open('x') as output:
        output.write(json.dumps(spec, indent=2) + '\n')
    observations = []
    server = ThreadingHTTPServer((host, args.port), partial(FixtureHandler, observations=observations, credential=credential))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        asyncio.run(run(trial_arguments(args, profile, smoke=True), credential=credential))
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    output = ROOT / '.raw/local-trials' / args.attempt
    receipt = json.loads((output / 'receipt.json').read_text())
    expected = spec['candidate']['generation']
    passed = (receipt['inference'] is False and receipt['status'] == 'verified'
              and receipt['verdict']['checks']['delivery'] is False
              and (output / 'raw-answer.json').read_bytes() == b'{}'
              and len(observations) == 2 and observations[-1]['tool_result_observed']
              and all(row['generation'] == expected for row in observations))
    proof = {'kind': 'scripted_native_harness_fixture', 'inference': False,
             'financial_evaluation': False, 'passed': passed, 'requests': observations,
             'authenticated': args.authenticated, 'endpoint': spec['serving']['base_url'],
             'expected_result': 'Native terminal writes invalid JSON workpaper. Separate verification rejects delivery.'}
    (output / 'transport-smoke.json').write_text(json.dumps(proof, indent=2) + '\n')
    if not passed:
        raise ValueError('native_transport_fixture_failed')
    print('Native transport, terminal execution, artifact retention and separate rejection verified. No inference.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('preflight')
    listing = commands.add_parser('list')
    listing.add_argument('--dataset', default='workflow-v8')
    listing.add_argument('--split', choices=('development', 'evaluation', 'all'), default='all')
    batching = commands.add_parser('batch')
    batching.add_argument('--dataset', default='workflow-v8')
    selection = batching.add_mutually_exclusive_group(required=True)
    selection.add_argument('--tasks', nargs='+')
    selection.add_argument('--split', choices=('development', 'evaluation', 'all'))
    batching.add_argument('--profile', type=Path, required=True)
    batching.add_argument('--attempt', required=True)
    for name in ('run', 'grade', 'smoke'):
        command = commands.add_parser(name)
        command.add_argument('--dataset', default='workflow-v8')
        command.add_argument('--task', default='c01')
        command.add_argument('--attempt', required=True)
        if name == 'run':
            command.add_argument('--profile', type=Path, required=True)
        elif name == 'grade':
            command.add_argument('--artifacts', type=Path, required=True)
        else:
            command.add_argument('--host')
            command.add_argument('--port', type=int, default=18080)
            command.add_argument('--authenticated', action='store_true')
    reporting = commands.add_parser('report')
    reporting.add_argument('--attempts', nargs='+', required=True)
    reporting.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'preflight':
        preflight()
    elif args.command == 'list':
        manifest = load(ROOT, args.dataset)
        for key in selected_tasks(args.dataset, split=args.split):
            print(key, manifest['tasks'][key].get('split', 'unspecified'))
    elif args.command == 'batch':
        batch(args)
    elif args.command == 'report':
        report(args.attempts, args.output)
    elif args.command == 'smoke':
        trial_arguments(args)
        smoke(args)
    else:
        preflight()
        asyncio.run(run(trial_arguments(args, getattr(args, 'profile', None))))


if __name__ == '__main__':
    main()
