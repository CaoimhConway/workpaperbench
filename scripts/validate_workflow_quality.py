"""Check authored workpapers in isolated Linux verifiers without inference."""
import argparse
import base64
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workpaperbench.catalog import load
from local_bench import BUILDER, digest, guest, prepare

DATASET = 'workflow-v5'
CONTAINER = '''import base64,json,pathlib,runpy,sys
payload=json.load(sys.stdin)
root=pathlib.Path('/logs/artifacts')
root.mkdir(parents=True)
for name,data in payload.items():
 (root/name).write_bytes(base64.b64decode(data,validate=True))
runpy.run_path('/tests/verify.py',run_name='__main__')
print(pathlib.Path('/logs/verifier/verdict.json').read_text())
'''
VERIFIER_BUILD = '''import pathlib,shutil,subprocess,sys,tempfile
with tempfile.TemporaryDirectory(prefix='wpb-quality-') as directory:
 context=pathlib.Path(directory)/'tests'
 shutil.copytree(sys.argv[1],context,copy_function=shutil.copy)
 subprocess.run(['docker','build','-q','-t',sys.argv[2],str(context)],check=True)
'''


def artifacts(task, variant, covered):
    answer = json.loads((task / 'tests/reference.json').read_text())
    gold = json.loads((task / 'tests/gold.json').read_text())
    files = {entry['file']: (task / 'solution' / entry['file']).read_text() for entry in answer['tables']}
    if variant == 'context':
        for role in ('tables', 'claims'):
            for entry in answer[role]:
                spec = gold[role][entry['id']]
                entry['evidence'] = sorted(set(spec['evidence'][-1] + spec['context_evidence_allowed']))
                if gold['scorer_version'] in ('workflow-1.2.0', 'workflow-1.2.1'):
                    entry['evidence'] = [' and '.join(entry['evidence']) + ' - supplied facts and context', 'Definition: see output_contract.json']
        for name, spec in gold['tables'].items():
            sql = files[name + '.sql'].strip().rstrip(';')
            expressions = []
            for column in reversed(spec['columns']):
                aliases = spec['columns'][column].get('aliases', {})
                if aliases:
                    cases = ' '.join("WHEN '" + value + "' THEN '" + alias + "'" for alias, value in aliases.items())
                    expressions.append('CASE "' + column + '" ' + cases + ' END AS "' + column + '"')
                else:
                    expressions.append('"' + column + '"')
            columns = ', '.join(expressions)
            files[name + '.sql'] = 'SELECT ' + columns + ' FROM (\n' + sql + '\n) ORDER BY 1 DESC\n'
    elif variant == 'always_unresolved':
        for entry in answer['claims']:
            entry['verdict'] = 'unresolved'
    elif variant == 'citation_dump':
        known = [entry['id'] for entry in json.loads((task / 'environment/evidence.json').read_text())]
        for entry in answer['tables'] + answer['claims']:
            entry['evidence'] = known
    elif variant == 'constant_residual':
        for name, spec in gold['tables'].items():
            forced = {column for table, column in covered if table == name}
            if forced:
                sql = files[name + '.sql'].strip().rstrip(';')
                columns = ', '.join(('0 AS ' if column in forced else '') + '"' + column + '"' for column in spec['columns'])
                files[name + '.sql'] = 'SELECT ' + columns + ' FROM (\n' + sql + '\n)\n'
    files['answer.json'] = json.dumps(answer, indent=2) + '\n'
    return {name: data.encode() for name, data in files.items()}


def expected(variant, revised=False):
    result = dict(financial_answer=variant != 'always_unresolved', evidence=variant != 'citation_dump',
                  robustness=variant != 'constant_residual', delivery=True)
    if revised:
        result.update(numerical_tables=True, claim_verdicts=variant != 'always_unresolved')
    return result


def validate(verdict, variant, covered):
    if verdict['checks'] != expected(variant, verdict['scorer_version'] in ('workflow-1.2.0', 'workflow-1.2.1')) or not all(verdict['isolation'].values()):
        raise ValueError('unexpected_quality_verdict:' + json.dumps(verdict))
    if variant == 'constant_residual':
        for name in {table for table, _ in covered}:
            checks = verdict['details']['tables'][name]
            assert checks['original']
            expected_failures = {'independent_disclosure_discrepancy'}
            if name == 'reserve_coverage' and 'reported_reserve_changes_with_components_fixed' in checks['controls']:
                expected_failures.add('reported_reserve_changes_with_components_fixed')
            assert {key for key, value in checks['controls'].items() if not value} == expected_failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', default='workflow-v11', choices=['workflow-v5', 'workflow-v6', 'workflow-v7', 'workflow-v8', 'workflow-v9', 'workflow-v10', 'workflow-v11', 'workflow-v12'])
    parser.add_argument('--executor', choices=['docker', 'local-lima'], default='docker',
                        help='Docker on this Linux controller, or the historical owner maintenance wrapper')
    parser.add_argument('--tasks', nargs='+', default=['a01', 'b01', 'c01'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-prefix', help='Also test these cases through native Harbor before the control sweep')
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('validation_report_already_exists')
    dataset = args.dataset
    if args.executor == 'docker':
        from guest_bench import preflight
        preflight()
    execute = (lambda *command, **kwargs: subprocess.run(list(command), check=True, **kwargs)) if args.executor == 'docker' else guest
    builder = str(ROOT) if args.executor == 'docker' else BUILDER
    manifest = load(ROOT, dataset)
    keys = list(manifest['tasks']) if args.tasks == ['all'] else args.tasks
    review = json.loads((ROOT / 'config/workflow-quality-review.json').read_text())
    report = {'validation_id': dataset + '-quality-1', 'manifest_id': manifest['manifest_id'],
              'scorer_version': manifest['scorer_version'], 'scorer_sha256': manifest['scorer_sha256'],
              'validator_sha256': digest(__file__), 'inference': False, 'external_service_spend_usd': 0,
              'scope': 'Authored positive and negative controls, not candidate-model performance',
              'native_receipts': [], 'isolated_verifier_checks': []}
    if args.native_prefix:
        for key in keys:
            _, _, task = load(ROOT, dataset, key)
            variant = 'reference'
            directory = ROOT / '.local/quality-submissions' / (args.native_prefix + '-' + key)
            directory.mkdir(parents=True, exist_ok=False)
            for name, data in artifacts(task, variant, []).items():
                (directory / name).write_bytes(data)
            attempt = args.native_prefix + '-' + key
            runner = 'guest_bench.py' if args.executor == 'docker' else 'local_bench.py'
            subprocess.run([sys.executable, str(ROOT / 'scripts' / runner), 'grade', '--dataset', dataset,
                '--task', key, '--artifacts', str(directory), '--attempt', attempt], check=True)
            path = ROOT / '.raw/local-trials' / attempt
            receipt = json.loads((path / 'receipt.json').read_text())
            assert receipt['manifest_id'] == manifest['manifest_id'] and not receipt['inference']
            assert digest(path / 'verifier.json') == receipt['verdict_sha256']
            assert digest(path / 'raw-answer.json') == receipt['raw_answer_sha256']
            for name, checksum in receipt['sql_file_sha256'].items():
                assert digest(path / 'raw-sql' / name) == checksum
            validate(receipt['verdict'], variant, [])
            report['native_receipts'].append({'receipt_sha256': digest(path / 'receipt.json'), 'receipt': receipt})
    (ROOT / '.local').mkdir(exist_ok=True)
    lock = (ROOT / '.local/local-command.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.executor == 'local-lima':
        prepare(dataset, keys)
    for key in keys:
        _, spec, task = load(ROOT, dataset, key)
        tag = 'wpb-quality-' + spec['task_sha256'][:16]
        # Fresh metadata prevents equal-sized archived databases from reusing
        # a stale build-context checksum. Frozen task files stay untouched.
        execute('python3', '-c', VERIFIER_BUILD, builder + '/' + spec['path'] + '/tests', tag, capture_output=True)
        image_id = execute('docker', 'image', 'inspect', '--format={{.Id}}', tag, capture_output=True).stdout.decode().strip()
        covered = review['residual_controls'].get(key, {}).get('covered', [])
        for variant in ['reference', 'context', 'citation_dump'] + (['constant_residual'] if covered else []) + (['always_unresolved'] if manifest['scorer_version'] in ('workflow-1.2.0', 'workflow-1.2.1') else []):
            files = artifacts(task, variant, covered)
            payload = json.dumps({name: base64.b64encode(data).decode() for name, data in files.items()}).encode()
            result = execute('docker', 'run', '--rm', '--network', 'none', '--read-only', '--memory', '384m',
                '--cpus', '1', '--pids-limit', '32', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--tmpfs', '/logs:rw,noexec,nosuid,size=4m', '--tmpfs', '/tmp:rw,noexec,nosuid,size=4m',
                '-i', image_id, 'python', '-c', CONTAINER, input=payload, capture_output=True)
            verdict = json.loads(result.stdout)
            try:
                validate(verdict, variant, covered)
                failure = None
            except (ValueError, AssertionError) as error:
                failure = str(error) or 'control_specific_expectation_failed'
                print(key, variant, 'FAILED', failure, flush=True)
            report['isolated_verifier_checks'].append({'task': key, 'task_sha256': spec['task_sha256'],
                'variant': variant, 'expectation_passed': failure is None, 'failure': failure, 'image_id': image_id, 'files_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
                'verdict': verdict})
        print(key, 'authored controls checked', flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as output:
        output.write(json.dumps(report, indent=2) + '\n')
    print(args.output)
    if any(not row['expectation_passed'] for row in report['isolated_verifier_checks']):
        raise SystemExit('Quality validation failed, inspect the retained diagnostic report')


if __name__ == '__main__':
    main()
