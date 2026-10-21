"""Verify specific frozen-ratio counterexamples in the existing isolated verifier."""
import argparse
import base64
import fcntl
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workpaperbench.catalog import load
from validate_workflow_quality import CONTAINER, VERIFIER_BUILD
from validate_workflow_contract_revision import DOCKER_LIMITS, execute_container
from workflow_dependency_cases import AUDIT_TARGETS, TARGETS, artifacts, validate_verdict


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(output):
    if platform.system() != 'Linux':
        raise ValueError('dependency_validation_requires_linux_docker_controller')
    report = {'validation_id': 'workflow-v11-dependencies-1', 'inference': False,
        'external_service_spend_usd': 0, 'environment': platform.platform(),
        'validator_sha256': digest(__file__),
        'cases_sha256': digest(ROOT / 'scripts/workflow_dependency_cases.py'),
        'container_limits': DOCKER_LIMITS, 'catalogs': {}, 'cases': [], 'status': 'running'}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        stream.write(json.dumps(report, indent=2) + '\n')
    (ROOT / '.local').mkdir(exist_ok=True)
    with (ROOT / '.local/local-command.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for dataset in ('workflow-v10', 'workflow-v11'):
            manifest = load(ROOT, dataset)
            report['catalogs'][dataset] = {name: manifest[name] for name in (
                'manifest_id', 'scorer_version', 'scorer_sha256', 'sql_worker_sha256')}
            report['catalogs'][dataset]['manifest_sha256'] = digest(ROOT / 'datasets' / dataset / 'manifest.json')
            for key in [*TARGETS, *(AUDIT_TARGETS if dataset == 'workflow-v10' else {})]:
                _, spec, task = load(ROOT, dataset, key)
                tag = 'wpb-dependency-' + spec['task_sha256'][:16]
                subprocess.run([sys.executable, '-c', VERIFIER_BUILD, str(task / 'tests'), tag],
                               check=True, capture_output=True, timeout=120)
                image_id = subprocess.check_output(['docker', 'image', 'inspect', '--format={{.Id}}', tag], text=True).strip()
                audit = key in AUDIT_TARGETS
                for case in (('frozen',) if audit else ('reference', 'alternative', 'frozen')):
                    files = artifacts(task, case, audit)
                    payload = json.dumps({name: base64.b64encode(raw).decode() for name, raw in files.items()}).encode()
                    result = execute_container(image_id, CONTAINER, payload)
                    result.check_returncode()
                    verdict = json.loads(result.stdout)
                    validate_verdict(verdict, key, case, dataset == 'workflow-v11', audit)
                    assert verdict['isolation'] and all(verdict['isolation'].values())
                    report['cases'].append({'dataset': dataset, 'task': key,
                        'task_sha256': spec['task_sha256'], 'case': case, 'audit': audit,
                        'image_id': image_id, 'artifact_sha256': {
                            name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()},
                        'expectation_passed': True, 'verdict': verdict})
                    print(dataset, key, case, 'expectation passed', flush=True)
                    output.write_text(json.dumps(report, indent=2) + '\n')
    report['status'] = 'passed'
    output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    validate(parser.parse_args().output.resolve())
