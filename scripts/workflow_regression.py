"""Check current workflow-v9 oracles and native agent transport without inference.

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
TASKS = ('a01', 'b01', 'b02', 'c01')


def run(binary, output):
    output = Path(output).resolve()
    details = output.parent / (output.stem + '-native')
    if output.exists() or details.exists():
        raise ValueError('regression_output_already_exists')
    if platform.system() != 'Linux':
        raise ValueError('regression_requires_linux_docker_controller')
    if subprocess.check_output([binary, '--version'], text=True, timeout=30,
                               env=native.child_environment()).strip() != '0.23.0':
        raise ValueError('unexpected_harbor_version')
    manifest = native.load(ROOT, 'workflow-v9')
    selected = {key: native.load(ROOT, 'workflow-v9', key)[1] for key in TASKS}
    details.mkdir(parents=True)
    report = {'kind': 'workflow_v9_native_regression', 'status': 'running',
        'harbor_version': '0.23.0', 'inference': False,
        'model_performance_evaluation': False, 'external_service_spend_usd': 0,
        'source': {'kind': 'checkout', 'manifest_id': manifest['manifest_id'],
            'manifest_sha256': hashlib.sha256((ROOT / 'datasets/workflow-v9/manifest.json').read_bytes()).hexdigest(),
            'tasks_sha256': {key: value['task_sha256'] for key, value in selected.items()}},
        'implementation_sha256': {name: hashlib.sha256((ROOT / 'scripts' / name).read_bytes()).hexdigest()
                                  for name in ('workflow_regression.py', 'validate_direct_harbor.py')},
        'oracles': [], 'agent_transport': None, 'error': None}
    output.write_text(json.dumps(report, indent=2) + '\n')
    try:
        jobs = details / 'jobs'
        command = [binary, 'run', *native.task_arguments(checkout=True),
                   '--agent', 'oracle', '-k', '1', '--n-concurrent', '1',
                   '--max-retries', '0', '--env', 'docker',
                   '--jobs-dir', str(jobs), '--job-name', 'oracles']
        for key in TASKS:
            command += ['-i', key]
        with (details / 'oracles.log').open('x') as log:
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT,
                           timeout=1800, env=native.child_environment())
        job_path = jobs / 'oracles/result.json'
        report['native_job_result_sha256'] = native.check_job(job_path, len(TASKS))
        trials = list((jobs / 'oracles').glob('*/result.json'))
        if len(trials) != len(TASKS):
            raise ValueError('unexpected_oracle_trial_count')
        seen = set()
        for path in trials:
            task_id = json.loads(path.read_text())['task_name'].removeprefix('workpaperbench/workflow-v9-')
            if task_id not in TASKS or task_id in seen:
                raise ValueError('unexpected_oracle_task_selection')
            seen.add(task_id)
            report['oracles'].append(native.check_trial(path, ROOT / native.TASKS / task_id, 1.0, checkout=True))
        report['agent_transport'] = native.validate(binary, details / 'agent-fixtures.json', checkout=True)
        for key in TASKS:
            current, current_spec, _ = native.load(ROOT, 'workflow-v9', key)
            if current['manifest_id'] != manifest['manifest_id'] or current_spec['task_sha256'] != selected[key]['task_sha256']:
                raise ValueError('regression_inputs_changed_during_execution')
        report['status'] = 'passed'
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        report['status'] = 'failed'
        report['error'] = type(error).__name__ + ':' + str(error)[:1000]
        raise
    finally:
        output.write_text(json.dumps(report, indent=2) + '\n')
    print('Workflow regression passed: four oracles and two scripted agent deliveries.')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harbor', default=shutil.which('harbor'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.harbor:
        parser.error('Harbor 0.23.0 must be installed')
    run(args.harbor, args.output)


if __name__ == '__main__':
    main()
