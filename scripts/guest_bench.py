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
from local_trial import clean_environment, external_configuration, run
from local_bench import report
from workpaperbench.catalog import load


def preflight():
    clean_environment()
    if platform.machine() != 'x86_64':
        raise ValueError('external_profile_requires_linux_x86_64_guest')
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
    bridge = subprocess.check_output(['docker', 'network', 'inspect', 'bridge'], text=True, timeout=30)
    if json.loads(bridge)[0]['IPAM']['Config'][0]['Gateway'] != '172.17.0.1':
        raise ValueError('external_docker_bridge_gateway')
    load(ROOT, 'workflow-v7')
    print('Dedicated Linux x86_64 guest, Docker bridge and Harbor 0.23.0 verified.')


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
    def __init__(self, *args, observations, **kwargs):
        self.observations = observations
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
    directory = ROOT / '.local'
    directory.mkdir(exist_ok=True)
    profile = directory / (args.attempt + '-transport-profile.json')
    with profile.open('x') as output:
        output.write(json.dumps(spec, indent=2) + '\n')
    observations = []
    server = ThreadingHTTPServer(('172.17.0.1', 18080), partial(FixtureHandler, observations=observations))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        asyncio.run(run(trial_arguments(args, profile, smoke=True)))
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
             'expected_result': 'Native terminal writes invalid JSON workpaper. Separate verification rejects delivery.'}
    (output / 'transport-smoke.json').write_text(json.dumps(proof, indent=2) + '\n')
    if not passed:
        raise ValueError('native_transport_fixture_failed')
    print('Native transport, terminal execution, artifact retention and separate rejection verified. No inference.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('preflight')
    for name in ('run', 'grade', 'smoke'):
        command = commands.add_parser(name)
        command.add_argument('--dataset', default='workflow-v7')
        command.add_argument('--task', default='c01')
        command.add_argument('--attempt', required=True)
        if name == 'run':
            command.add_argument('--profile', type=Path, required=True)
        elif name == 'grade':
            command.add_argument('--artifacts', type=Path, required=True)
    reporting = commands.add_parser('report')
    reporting.add_argument('--attempts', nargs='+', required=True)
    reporting.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'preflight':
        preflight()
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
