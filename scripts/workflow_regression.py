"""Check current workflow oracles and native agent transport without inference.

Run on a Linux Docker controller:
python scripts/workflow_regression.py --output .local/workflow-regression.json
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess

import validate_direct_harbor as native

ROOT = native.ROOT
TASKS = ('a01', 'b01', 'b02', 'b06', 'c01')


def run(binary, output, dataset='workflow-v15'):
    output = Path(output).resolve()
    details = output.parent / (output.stem + '-native')
    if output.exists() or details.exists():
        raise ValueError('regression_output_already_exists')
    if platform.system() != 'Linux':
        raise ValueError('regression_requires_linux_docker_controller')
    if subprocess.check_output([binary, '--version'], text=True, timeout=30,
                               env=native.child_environment()).strip() != '0.23.0':
        raise ValueError('unexpected_harbor_version')
    manifest = native.load(ROOT, dataset)
    selected = {key: native.load(ROOT, dataset, key)[1] for key in TASKS}
    details.mkdir(parents=True)
    report = {'kind': 'workflow_native_regression', 'status': 'running',
        'harbor_version': '0.23.0', 'inference': False,
        'model_performance_evaluation': False, 'external_service_spend_usd': 0,
        'source': {'kind': 'checkout', 'manifest_id': manifest['manifest_id'],
            'manifest_sha256': hashlib.sha256((ROOT / 'datasets' / dataset / 'manifest.json').read_bytes()).hexdigest(),
            'tasks_sha256': {key: value['task_sha256'] for key, value in selected.items()}},
        'implementation_sha256': {name: hashlib.sha256((ROOT / 'scripts' / name).read_bytes()).hexdigest()
                                  for name in ('workflow_regression.py', 'validate_direct_harbor.py')},
        'native_job_results_sha256': {}, 'oracles': [], 'agent_transport': None, 'error': None}
    output.write_text(json.dumps(report, indent=2) + '\n')
    try:
        jobs = details / 'jobs'
        for key in TASKS:
            command = [binary, 'run', *native.task_arguments(checkout=True, dataset=dataset),
                       '-i', key, '--agent', 'oracle', '-k', '1', '--n-concurrent', '1',
                       '--max-retries', '0', *native.environment_arguments(manifest, selected[key], checkout=True),
                       '--jobs-dir', str(jobs), '--job-name', key]
            with (details / (key + '.log')).open('x') as log:
                subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT,
                               timeout=600, env=native.child_environment())
            report['native_job_results_sha256'][key] = native.check_job(jobs / key / 'result.json', 1)
            trials = list((jobs / key).glob('*/result.json'))
            if len(trials) != 1:
                raise ValueError('unexpected_oracle_trial_count')
            report['oracles'].append(native.check_trial(
                trials[0], ROOT / 'datasets' / dataset / 'tasks' / key, 1.0, checkout=True))
        report['agent_transport'] = native.validate(binary, details / 'agent-fixtures.json', checkout=True, dataset=dataset)
        for key in TASKS:
            current, current_spec, _ = native.load(ROOT, dataset, key)
            if current['manifest_id'] != manifest['manifest_id'] or current_spec['task_sha256'] != selected[key]['task_sha256']:
                raise ValueError('regression_inputs_changed_during_execution')
        report['status'] = 'passed'
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        report['status'] = 'failed'
        report['error'] = type(error).__name__ + ':' + str(error)[:1000]
        raise
    finally:
        output.write_text(json.dumps(report, indent=2) + '\n')
    print('Workflow regression passed: five oracles and two scripted agent deliveries.')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harbor', default=shutil.which('harbor'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dataset', default='workflow-v15')
    args = parser.parse_args()
    if not args.harbor:
        parser.error('Harbor 0.23.0 must be installed')
    run(args.harbor, args.output, args.dataset)


if __name__ == '__main__':
    main()
