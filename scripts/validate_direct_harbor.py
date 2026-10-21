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
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workpaperbench.catalog import load

REPO = 'CaoimhConway/workpaperbench@v0.6.3-rc.1'
TASKS = 'datasets/workflow-v11/tasks'
MODEL = 'workpaperbench-direct-fixture'
KEY = 'fixture-only-no-provider-credential'
MARKER = 'WPB_DIRECT_AGENT_OK'
DIMENSIONS = ('financial_answer', 'numerical_tables', 'claim_verdicts',
              'evidence', 'robustness', 'delivery')
ISOLATION = ('network_probe_blocked', 'network_namespace_none',
             'no_inference_key', 'no_docker_socket')


def task_arguments(checkout=False):
    return ['-p', str(ROOT / TASKS)] if checkout else ['--repo', REPO, '-p', TASKS]


def child_environment():
    return {name: value for name, value in os.environ.items()
            if not name.endswith('API_KEY') and name not in ('GH_TOKEN', 'GITHUB_TOKEN')}


def check_job(path, count):
    job = json.loads(path.read_text())
    stats = job['stats']
    wanted = dict(n_completed_trials=count, n_errored_trials=0, n_running_trials=0,
                  n_pending_trials=0, n_cancelled_trials=0, n_retries=0)
    if (type(job.get('n_total_trials')) is not int or job['n_total_trials'] != count or
            any(type(stats.get(key)) is not int or stats[key] != value for key, value in wanted.items())):
        raise ValueError('unexpected_native_job_counts')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_trial(path, task, reward, checkout=False):
    """Require native results, exact delivery and the separate verifier diagnostics."""
    trial = json.loads(path.read_text())
    verdict_path = path.parent / 'verifier/verdict.json'
    verdict = json.loads(verdict_path.read_text())
    reference = json.loads((task / 'tests/reference.json').read_text())
    gold = json.loads((task / 'tests/gold.json').read_text())
    positive = reward == 1
    wanted = {name: True if positive else None for name in DIMENSIONS}
    wanted['delivery'] = positive
    rewards = trial.get('verifier_result', {}).get('rewards', {})
    if (trial.get('task_name') != 'workpaperbench/' + reference['task_id'] or
            'exception_info' not in trial or trial['exception_info'] is not None or
            trial.get('verifier_environment_mode') != 'separate' or
            set(rewards) != {'reward'} or type(rewards['reward']) not in (int, float) or
            rewards['reward'] != reward):
        raise ValueError('unexpected_native_trial_result')
    if checkout:
        source = trial['config']['task']
        if source.get('git_url') or Path(source['path']).resolve() != task.resolve():
            raise ValueError('native_trial_did_not_use_checkout')
    checks, isolation = verdict.get('checks', {}), verdict.get('isolation', {})
    errors = verdict.get('errors')
    if (verdict.get('scorer_version') != gold['scorer_version'] or
            verdict.get('complete') is not positive or set(checks) != set(DIMENSIONS) or
            any(checks[name] is not wanted[name] for name in DIMENSIONS) or
            set(isolation) != set(ISOLATION) or any(value is not True for value in isolation.values()) or
            not isinstance(errors, list) or (errors if positive else
                not errors or any(not isinstance(error, str) or not error.startswith('delivery:') for error in errors))):
        raise ValueError('unexpected_verifier_diagnostics')
    details = verdict['details']
    if positive:
        controls = {row['name'] for row in gold['controls']}
        if (set(details['tables']) != {row['id'] for row in reference['tables']} or
                set(details['claims']) != {row['id'] for row in reference['claims']}):
            raise ValueError('missing_financial_diagnostics')
        for row in details['tables'].values():
            if (row['original'] is not True or row['evidence'] is not True or
                    set(row['controls']) != controls or any(value is not True for value in row['controls'].values())):
                raise ValueError('unexpected_table_diagnostics')
        if any(row['verdict'] is not True or row['evidence'] is not True for row in details['claims'].values()):
            raise ValueError('unexpected_claim_diagnostics')
    elif details['tables'] or details['claims']:
        raise ValueError('unexpected_invalid_delivery_diagnostics')
    retained = path.parent / 'artifacts/logs/artifacts'
    answer = retained / 'answer.json'
    if json.loads(answer.read_text()) != (reference if positive else {}):
        raise ValueError('unexpected_retained_answer')
    files = {'answer.json', *(row['file'] for row in reference['tables'])} if positive else {'answer.json'}
    if {file.name for file in retained.iterdir()} != files:
        raise ValueError('unexpected_retained_files')
    sql = {}
    for name in files - {'answer.json'}:
        data = (retained / name).read_bytes()
        if data != (task / 'solution' / name).read_bytes():
            raise ValueError('unexpected_retained_sql')
        sql[name] = hashlib.sha256(data).hexdigest()
    return {'task': reference['task_id'], 'reward': reward, 'isolation': isolation,
        'native_result_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'verdict_sha256': hashlib.sha256(verdict_path.read_bytes()).hexdigest(),
        'retained_answer_sha256': hashlib.sha256(answer.read_bytes()).hexdigest(),
        'retained_sql_sha256': sql}


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
    def __init__(self, *args, commands, requests, expected_generation=None, **kwargs):
        self.commands = commands
        self.requests = requests
        self.expected_generation = expected_generation
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
        generation = {'max_tokens': request.get('max_completion_tokens', request.get('max_tokens')),
                      'reasoning_effort': request.get('reasoning_effort')}
        if self.expected_generation is not None and generation != self.expected_generation:
            self.send_error(400)
            return
        observed = any(row.get('role') == 'user' and MARKER in str(row.get('content'))
                       for row in request['messages'])
        observation = {'terminal_completion_observed': observed}
        if self.expected_generation is not None:
            observation['generation'] = generation
        self.requests.append(observation)
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


def validate(binary, output, checkout=False, comparison_recipe=False):
    if output.exists() or output.parent.joinpath(output.stem + '-jobs').exists():
        raise ValueError('validation_output_already_exists')
    if subprocess.check_output([binary, '--version'], text=True, timeout=30,
                               env=child_environment()).strip() != '0.23.0':
        raise ValueError('unexpected_harbor_version')
    manifest, spec, task = load(ROOT, 'workflow-v11', 'c01')
    recipe = None
    if comparison_recipe:
        recipe = json.loads((ROOT / 'config/construction-comparison.json').read_text())
        if recipe['task_source']['manifest_id'] != manifest['manifest_id']:
            raise ValueError('comparison_recipe_catalog_mismatch')
    output.parent.mkdir(parents=True, exist_ok=True)
    jobs = output.parent / (output.stem + '-jobs')
    results = []
    for variant, expected in [('reference', 1.0), ('invalid', 0.0)]:
        requests = []
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Fixture,
            commands=command(task, variant), requests=requests,
            expected_generation={'max_tokens': recipe['runtime']['agent_kwargs']['llm_call_kwargs']['max_tokens'],
                                 'reasoning_effort': recipe['runtime']['agent_kwargs']['reasoning_effort']} if recipe else None))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        endpoint = f'http://127.0.0.1:{server.server_port}/v1'
        model_info = {'max_input_tokens': 65536, 'max_output_tokens': 4096,
            'input_cost_per_token': 0, 'output_cost_per_token': 0,
            'litellm_provider': 'openai', 'mode': 'chat'}
        arguments = [binary, 'run', *task_arguments(checkout), '-i', 'c01',
            '--agent', 'terminus-2', '--model', 'openai/' + MODEL,
            '--ak', 'api_base=' + endpoint,
            '--ae', 'WPB_DIRECT_FIXTURE_API_KEY=' + KEY,
            '--n-concurrent', '1', '--max-retries', '0', '--env', 'docker', '--jobs-dir', str(jobs),
            '--job-name', variant]
        options = {'max_turns': 5, 'model_info': model_info}
        if recipe:
            options.update(recipe['runtime']['agent_kwargs'])
            options['model_info'] = {**model_info, **options['model_info']}
            arguments += ['--agent-timeout-multiplier', str(recipe['runtime']['agent_timeout_multiplier'])]
        for name, value in options.items():
            encoded = json.dumps(value) if not isinstance(value, str) else value
            arguments += ['--ak', name + '=' + encoded]
        environment = dict(child_environment(), OPENAI_API_KEY=KEY)
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
        job_sha256 = check_job(jobs / variant / 'result.json', 1)
        trial_paths = list((jobs / variant).glob('*/result.json'))
        if len(trial_paths) != 1:
            raise ValueError('unexpected_native_trial_count')
        result = check_trial(trial_paths[0], task, expected, checkout)
        if not requests or requests[-1]['terminal_completion_observed'] is not True:
            raise ValueError('native_terminal_feedback_missing')
        results.append({'variant': variant, 'agent': 'terminus-2',
            **result, 'native_job_result_sha256': job_sha256, 'requests': requests,
            'candidate_received_test_key': True, 'candidate_external_tls_probe_blocked': True,
            'candidate_reference_paths_absent': True})
    current, current_spec, _ = load(ROOT, 'workflow-v11', 'c01')
    if current['manifest_id'] != manifest['manifest_id'] or current_spec['task_sha256'] != spec['task_sha256']:
        raise ValueError('fixture_inputs_changed_during_execution')
    report = {'kind': 'scripted_native_harbor_agent_fixture', 'harbor_version': '0.23.0',
        'repo': REPO, 'inference': False, 'model_performance_evaluation': False,
        'external_service_spend_usd': 0, 'cases': results}
    if recipe:
        report['comparison_recipe'] = {'protocol_version': recipe['protocol_version'],
            'configuration_sha256': hashlib.sha256((ROOT / 'config/construction-comparison.json').read_bytes()).hexdigest(),
            'agent_kwargs': recipe['runtime']['agent_kwargs']}
    if checkout:
        report['repo'] = None
        report['source'] = {'kind': 'checkout', 'manifest_id': manifest['manifest_id'],
                            'task_sha256': spec['task_sha256']}
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harbor', default=shutil.which('harbor'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--checkout', action='store_true',
                        help='Run the current checkout task bytes instead of the pinned public release')
    parser.add_argument('--comparison-recipe', action='store_true',
                        help='Check the frozen comparison settings with scripted responses, without inference')
    args = parser.parse_args()
    if not args.harbor:
        raise ValueError('harbor_not_installed')
    validate(args.harbor, args.output.resolve(), args.checkout, args.comparison_recipe)


if __name__ == '__main__':
    main()
