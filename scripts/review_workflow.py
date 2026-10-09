"""Reconstruct an explicitly versioned review of the unchanged workflow-v5 tasks."""
import argparse
import base64
import copy
import fcntl
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workpaperbench.catalog import load, tree_hash
from local_bench import guest, digest
from validate_workflow_quality import CONTAINER

SCORER = 'config/scorers/workflow-1.2.0.py'
# Full category names come from the supplied filing, not from a candidate answer.
BLOCK_LABELS = {
    'Transaction-based revenue': 'transaction',
    'Subscription and services-based revenue': 'subscription',
    'Hardware revenue': 'hardware',
    'Bitcoin revenue': 'bitcoin',
    'Amortization of acquired technology assets': 'acquired_technology_amortization',
}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def reviewed_task(source, target, key, historical=True):
    shutil.copytree(source, target)
    gold = json.loads((target / 'tests/gold.json').read_text())
    gold['scorer_version'] = 'workflow-1.2.0'
    for name, spec in gold['tables'].items():
        for index, (column, declaration) in enumerate(spec['columns'].items()):
            if declaration['type'] != 'text':
                continue
            declaration['values'] = sorted({row[index] for row in spec['rows']})
            if key == 'c01' and column == 'category':
                declaration['aliases'] = {alias: value for alias, value in BLOCK_LABELS.items()
                                          if value in declaration['values']}
    if historical:
        # These assertions conflate absence of identification with unknown value.
        # Either reading is defensible. This does not apply to rewritten v6 claims.
        for spec in gold['claims'].values():
            if spec['verdict'] == 'unresolved':
                spec['accepted_verdicts'] = ['unresolved', 'contradicted']
    shutil.copyfile(ROOT / SCORER, target / 'tests/workpaperbench/workflow_grading.py')
    seal(target, gold)
    return gold


def seal(task, gold):
    gold['hashes'] = {path.relative_to(task / 'tests').as_posix(): digest(path)
                     for path in sorted((task / 'tests').rglob('*'))
                     if path.is_file() and path.name not in ('gold.json', 'reference.json')}
    write_json(task / 'tests/gold.json', gold)


def isolated(task, files):
    """Use the established networkless verifier in the dedicated Linux guest."""
    identity = tree_hash(task)
    folder = '/home/wpb/workflow-reviews/' + identity
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w') as bundle:
        for path in sorted((task / 'tests').rglob('*')):
            if path.is_file():
                bundle.add(path, arcname=path.relative_to(task / 'tests').as_posix(), recursive=False)
    guest('mkdir', '-p', folder)
    guest('tar', '-xf', '-', '-C', folder, input=archive.getvalue())
    tag = 'wpb-review-' + identity[:16]
    guest('docker', 'build', '-q', '-t', tag, folder, capture_output=True)
    image = guest('docker', 'image', 'inspect', '--format={{.Id}}', tag, capture_output=True).stdout.decode().strip()
    payload = json.dumps({name: base64.b64encode(raw).decode() for name, raw in files.items()}).encode()
    result = guest('docker', 'run', '--rm', '--network', 'none', '--read-only', '--memory', '384m',
        '--cpus', '1', '--pids-limit', '32', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--tmpfs', '/logs:rw,noexec,nosuid,size=4m', '--tmpfs', '/tmp:rw,noexec,nosuid,size=4m',
        '-i', image, 'python', '-c', CONTAINER, input=payload, capture_output=True)
    verdict = json.loads(result.stdout)
    if not all(verdict['isolation'].values()):
        raise ValueError('review_isolation_failed')
    return {'reviewed_task_sha256': identity, 'image_id': image, 'verdict': verdict}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--submissions', type=Path, default=ROOT / 'reports/workflow-v5/submissions')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('review_report_already_exists')
    base = load(ROOT, 'workflow-v5')
    report = {'review_id': 'workflow-v5-scoring-1', 'base_manifest_id': base['manifest_id'],
              'scorer_version': 'workflow-1.2.0', 'scorer_sha256': digest(ROOT / SCORER),
              'review_script_sha256': digest(__file__), 'inference': False,
              'external_service_spend_usd': 0,
              'scope': 'Corrected replay of exact retained development artifacts, not new model runs or workflow-v6 results',
              'attempts': []}
    (ROOT / '.local').mkdir(exist_ok=True)
    with (ROOT / '.local/local-command.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for directory in sorted(args.submissions.iterdir()):
            receipt = json.loads((directory / 'receipt.json').read_text())
            key = receipt['task_id'].rsplit('-', 1)[1]
            _, spec, source = load(ROOT, 'workflow-v5', key)
            if receipt['manifest_id'] != base['manifest_id'] or receipt['task_sha256'] != spec['task_sha256']:
                raise ValueError('original_task_changed')
            files = {'answer.json': (directory / 'answer.json').read_bytes()}
            files.update({name: (directory / name).read_bytes() for name in receipt['sql_file_sha256']})
            hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
            if hashes.pop('answer.json') != receipt['raw_answer_sha256'] or hashes != receipt['sql_file_sha256']:
                raise ValueError('original_submission_changed')
            with tempfile.TemporaryDirectory() as temp:
                task = Path(temp) / 'task'
                reviewed_task(source, task, key)
                review = isolated(task, files)
            report['attempts'].append({'attempt_id': receipt['attempt_id'], 'task': key,
                'original_receipt_sha256': digest(directory / 'receipt.json'),
                'original_task_sha256': spec['task_sha256'],
                'files_sha256': {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()},
                'original_verdict': receipt['verdict'], **review})
            print(receipt['attempt_id'], review['verdict']['checks'], flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as output:
        output.write(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
