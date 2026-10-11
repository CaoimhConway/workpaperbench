"""Exercise the native Harbor agent interface with a local scripted endpoint."""
import argparse
import base64
from functools import partial
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading

ROOT = Path(__file__).resolve().parents[1]
REPO = 'CaoimhConway/workpaperbench@v0.6.0-rc.1'
TASKS = 'datasets/workflow-v8/tasks'
MODEL = 'workpaperbench-direct-fixture'
KEY = 'fixture-only-no-provider-credential'
MARKER = 'WPB_DIRECT_AGENT_OK'


def command(task, variant):
    answer = json.loads((task / 'tests/reference.json').read_text())
    files = {'answer.json': json.dumps(answer)}
    files.update({row['file']: (task / 'solution' / row['file']).read_text()
                  for row in answer['tables']})
    if variant == 'invalid':
        files = {'answer.json': '{}'}
    payload = base64.b64encode(json.dumps(files).encode()).decode()
    script = f'''import base64,json,os,socket,ssl
from pathlib import Path
assert os.environ.get('WPB_DIRECT_FIXTURE_API_KEY') == {KEY!r}
assert not any(name in os.environ for name in ('GH_TOKEN','GITHUB_TOKEN'))
assert not any(Path(name).exists() for name in ('/tests','/solution','/workspace/.git','/var/run/docker.sock'))
try:
    with socket.create_connection(('1.1.1.1',443),timeout=2) as connection:
        with ssl.create_default_context().wrap_socket(connection,server_hostname='one.one.one.one'):
            pass
except OSError:
    pass
else:
    raise RuntimeError('candidate_external_tls_probe')
root=Path('/logs/artifacts')
root.mkdir(parents=True,exist_ok=True)
for name,data in json.loads(base64.b64decode({payload!r})).items():
    (root/name).write_text(data)
print({MARKER!r},flush=True)
'''
    encoded = base64.b64encode(script.encode()).decode()
    return f"python -c \"import base64; exec(base64.b64decode('{encoded}'))\"\n"


class Fixture(BaseHTTPRequestHandler):
    def __init__(self, *args, commands, requests, **kwargs):
        self.commands = commands
        self.requests = requests
        super().__init__(*args, **kwargs)

    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.path != '/v1/chat/completions' or self.headers.get('Authorization') != 'Bearer ' + KEY:
            self.send_error(401)
            return
        size = int(self.headers.get('Content-Length', '0'))
        if not 0 < size <= 500000 or len(self.requests) >= 5:
            self.send_error(400)
            return
        request = json.loads(self.rfile.read(size))
        if request.get('model') != MODEL:
            self.send_error(400)
            return
        observed = any(row.get('role') == 'user' and MARKER in str(row.get('content'))
                       for row in request['messages'])
        self.requests.append({'terminal_completion_observed': observed})
        content = json.dumps({'analysis': 'Scripted protocol fixture.',
            'plan': 'Deliver the verifier fixture.' if not observed else 'Finish the fixture.',
            'commands': [] if observed else [{'keystrokes': self.commands, 'duration': 3.0}],
            'task_complete': observed})
        response = {'id': 'wpb-direct-fixture', 'object': 'chat.completion', 'created': 0,
            'model': MODEL, 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': content},
                                      'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}}
        body = json.dumps(response).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def validate(binary, output):
    if output.exists() or output.parent.joinpath(output.stem + '-jobs').exists():
        raise ValueError('validation_output_already_exists')
    if subprocess.check_output([binary, '--version'], text=True).strip() != '0.23.0':
        raise ValueError('unexpected_harbor_version')
    output.parent.mkdir(parents=True, exist_ok=True)
    jobs = output.parent / (output.stem + '-jobs')
    task = ROOT / TASKS / 'c01'
    results = []
    for variant, expected in [('reference', 1.0), ('invalid', 0.0)]:
        requests = []
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Fixture,
            commands=command(task, variant), requests=requests))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        endpoint = f'http://127.0.0.1:{server.server_port}/v1'
        model_info = {'max_input_tokens': 65536, 'max_output_tokens': 4096,
            'input_cost_per_token': 0, 'output_cost_per_token': 0,
            'litellm_provider': 'openai', 'mode': 'chat'}
        arguments = [binary, 'run', '--repo', REPO, '-p', TASKS, '-i', 'c01',
            '--agent', 'terminus-2', '--model', 'openai/' + MODEL,
            '--ak', 'api_base=' + endpoint, '--ak', 'max_turns=5',
            '--ak', 'model_info=' + json.dumps(model_info),
            '--ae', 'WPB_DIRECT_FIXTURE_API_KEY=' + KEY,
            '--n-concurrent', '1', '--env', 'docker', '--jobs-dir', str(jobs),
            '--job-name', variant]
        environment = dict(os.environ, OPENAI_API_KEY=KEY)
        try:
            with (output.parent / (output.stem + '-' + variant + '.log')).open('x') as log:
                process = subprocess.run(arguments, env=environment, stdout=log,
                                         stderr=subprocess.STDOUT, timeout=600)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)
        if process.returncode:
            raise ValueError('native_agent_execution_failed:' + variant)
        trial_paths = list((jobs / variant).glob('*/result.json'))
        assert len(trial_paths) == 1
        trial = json.loads(trial_paths[0].read_text())
        assert trial['exception_info'] is None, trial['exception_info']
        assert trial['verifier_result']['rewards']['reward'] == expected
        verifier = trial_paths[0].parent / 'verifier/verdict.json'
        verdict = json.loads(verifier.read_text())
        assert all(verdict['isolation'].values())
        assert verdict['checks']['delivery'] is (variant == 'reference')
        assert requests and requests[-1]['terminal_completion_observed']
        retained = trial_paths[0].parent / 'artifacts/logs/artifacts/answer.json'
        assert json.loads(retained.read_text()) == (json.loads((task / 'tests/reference.json').read_text()) if expected else {})
        results.append({'variant': variant, 'agent': 'terminus-2',
            'task': 'workflow-v8-c01', 'reward': expected, 'requests': requests,
            'candidate_received_test_key': True, 'candidate_external_tls_probe_blocked': True,
            'candidate_reference_paths_absent': True, 'isolation': verdict['isolation'],
            'verdict_sha256': hashlib.sha256(verifier.read_bytes()).hexdigest(),
            'retained_answer_sha256': hashlib.sha256(retained.read_bytes()).hexdigest()})
    report = {'kind': 'scripted_native_harbor_agent_fixture', 'harbor_version': '0.23.0',
        'repo': REPO, 'inference': False, 'model_performance_evaluation': False,
        'external_service_spend_usd': 0, 'cases': results}
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harbor', default=shutil.which('harbor'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.harbor:
        raise ValueError('harbor_not_installed')
    validate(args.harbor, args.output.resolve())


if __name__ == '__main__':
    main()
