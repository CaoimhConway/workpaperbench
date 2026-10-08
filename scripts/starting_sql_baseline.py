"""Assess unchanged starting SQL with frozen scorers in the existing verifier."""
import argparse
import base64
from collections import Counter
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from workpaperbench.catalog import load, tree_hash
from local_bench import digest, guest
from review_workflow import isolated, reviewed_task

# Run the frozen verifier's boundary probe first. No answer.json is supplied.
# Then use its unchanged SQL worker and comparison function for tables alone.
CONTAINER = '''import base64,json,pathlib,runpy,sys
payload=json.load(sys.stdin)
root=pathlib.Path('/logs/artifacts')
root.mkdir(parents=True)
for name,data in payload.items():
 (root/name).write_bytes(base64.b64decode(data,validate=True))
runpy.run_path('/tests/verify.py',run_name='__main__')
boundary=json.loads(pathlib.Path('/logs/verifier/verdict.json').read_text())
assert all(boundary['isolation'].values())
from workpaperbench import workflow_grading as scorer
trusted=pathlib.Path('/tests')
gold=json.loads((trusted/'gold.json').read_text())
assert all(scorer.digest(trusted/name)==value for name,value in gold['hashes'].items())
tables={}
for name,spec in gold['tables'].items():
 sql=(root/(name+'.sql')).read_text()
 def check(database,rows):
  actual=scorer.replay(sql,trusted/database)
  error=scorer.comparison_error(actual,spec,rows) if hasattr(scorer,'comparison_error') else (None if scorer.compare(actual,spec,rows) else 'mismatch')
  return error
 original=check('data.sqlite',spec['rows'])
 errors={control['name']:check(control['database'],control['tables'][name]) for control in gold['controls']}
 tables[name]={'original':original is None,'original_error':original,
  'controls':{key:value is None for key,value in errors.items()},'control_errors':errors}
print(json.dumps({'scorer_version':gold['scorer_version'],'details':{'tables':tables},'isolation':boundary['isolation']}))
'''


def transition(before, after):
    if type(before) is not bool or type(after) is not bool:
        raise ValueError('unscored_transition')
    return {(False, True): 'Repair', (True, True): 'Preservation',
            (True, False): 'Regression', (False, False): 'Unrepaired'}[before, after]


def classify(before, after):
    if set(before['controls']) != set(after['controls']):
        raise ValueError('incomparable_controls')
    initial = before['original'] and all(before['controls'].values())
    final = after['original'] and all(after['controls'].values())
    return transition(before['original'], after['original']), transition(initial, final)


def baseline(task):
    reference = json.loads((task / 'tests/reference.json').read_text())
    files = {entry['file']: (task / 'environment' / ('starting_' + entry['file'])).read_bytes()
             for entry in reference['tables']}
    result = isolated(task, files)
    payload = json.dumps({name: base64.b64encode(raw).decode() for name, raw in files.items()}).encode()
    response = guest('docker', 'run', '--rm', '--network', 'none', '--read-only', '--memory', '384m',
        '--cpus', '1', '--pids-limit', '32', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--tmpfs', '/logs:rw,noexec,nosuid,size=4m', '--tmpfs', '/tmp:rw,noexec,nosuid,size=4m',
        '-i', result['image_id'], 'python', '-c', CONTAINER, input=payload, capture_output=True)
    result['verdict'] = json.loads(response.stdout)
    if not all(result['verdict']['isolation'].values()):
        raise ValueError('baseline_isolation_failed')
    result['byte_identical'] = {entry['id']: files[entry['file']] == (task / 'solution' / entry['file']).read_bytes()
                                for entry in reference['tables']}
    return result


def retained():
    """Only complete deliveries with retained table verdicts are comparable here."""
    corrected_path = ROOT / 'reports/workflow-v5/corrected-replay.json'
    corrected = json.loads(corrected_path.read_text())
    manifest = load(ROOT, 'workflow-v5')
    if (corrected['base_manifest_id'] != manifest['manifest_id']
            or corrected['scorer_sha256'] != digest(ROOT / 'config/scorers/workflow-1.2.0.py')):
        raise ValueError('corrected_replay_identity')
    entries = []
    for attempt in corrected['attempts']:
        directory = ROOT / 'reports/workflow-v5/submissions' / attempt['attempt_id']
        receipt = json.loads((directory / 'receipt.json').read_text())
        _, spec, _ = load(ROOT, 'workflow-v5', attempt['task'])
        if (digest(directory / 'receipt.json') != attempt['original_receipt_sha256']
                or receipt['task_sha256'] != spec['task_sha256']
                or receipt['manifest_id'] != manifest['manifest_id']
                or receipt['verdict'] != attempt['original_verdict']):
            raise ValueError('retained_receipt_identity')
        for name, expected in attempt['files_sha256'].items():
            if digest(directory / name) != expected:
                raise ValueError('retained_submission_changed')
        entries.append(('workflow-v5', attempt['task'], attempt, corrected_path))
    # Earlier valid delivery. Incomplete and interrupted attempts have no
    # comparable whole-delivery table verdicts and remain explicitly unscored.
    path = ROOT / 'reports/local/workflow-development-budget-diagnostics-1.json'
    report = json.loads(path.read_text())
    manifest = load(ROOT, 'workflow-v4')
    if report['manifest_id'] != manifest['manifest_id'] or report['scorer_sha256'] != manifest['scorer_sha256']:
        raise ValueError('historical_report_identity')
    for attempt in report['scored_attempts']:
        if attempt['checks']['delivery'] is True and attempt['details']['tables']:
            key = attempt['task_id'].rsplit('-', 1)[1]
            entries.append(('workflow-v4', key, {'attempt_id': attempt['attempt_id'],
                'original_verdict': {'details': attempt['details'], 'checks': attempt['checks']},
                'original_receipt_sha256': attempt['receipt_sha256']}, path))
    return corrected, entries


def state(item):
    failed = [name + ':' + str(item['control_errors'][name])
              for name, passed in item['controls'].items() if not passed]
    return ('pass' if item['original'] else 'fail:' + str(item['original_error']),
            str(sum(item['controls'].values())) + '/' + str(len(item['controls'])), ', '.join(failed) or '-')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('baseline_report_already_exists')
    manifest = load(ROOT, 'workflow-v6')
    corrected, entries = retained()
    results, historical, identities = {}, {}, []
    (ROOT / '.local').mkdir(exist_ok=True)
    with (ROOT / '.local/local-command.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for key in sorted(manifest['tasks']):
            _, spec, task = load(ROOT, 'workflow-v6', key)
            results[key] = baseline(task)
            identities.append(('workflow-v6/' + key, spec['task_sha256'], results[key]['image_id']))
            print(key, 'starting SQL checked', flush=True)
        for dataset, key in sorted({(dataset, key) for dataset, key, _, _ in entries}):
            _, spec, task = load(ROOT, dataset, key)
            historical[dataset, key, 'original'] = baseline(task)
            identities.append((dataset + '/' + key, spec['task_sha256'], historical[dataset, key, 'original']['image_id']))
            if dataset == 'workflow-v5':
                with tempfile.TemporaryDirectory() as temp:
                    target = Path(temp) / 'task'
                    reviewed_task(task, target, key)
                    result = baseline(target)
                    expected = next(entry['reviewed_task_sha256'] for _, k, entry, _ in entries if k == key)
                    if tree_hash(target) != expected:
                        raise ValueError('corrected_task_identity')
                historical[dataset, key, 'corrected'] = result
                identities.append((dataset + '/' + key + '-corrected', expected, result['image_id']))
            print(dataset, key, 'historical starting SQL checked', flush=True)
    tables = [item for result in results.values() for item in result['verdict']['details']['tables'].values()]
    same = sum(sum(result['byte_identical'].values()) for result in results.values())
    original = sum(item['original'] for item in tables)
    robust = sum(item['original'] and all(item['controls'].values()) for item in tables)
    no_repair = [key for key, result in results.items()
                 if all(item['original'] and all(item['controls'].values()) for item in result['verdict']['details']['tables'].values())]
    lines = ['# Unchanged starting SQL and retained transitions', '',
        f'Current catalog `{manifest["manifest_id"]}`, scorer `{manifest["scorer_version"]}`.',
        f'**{same}/{len(tables)} queries are byte-identical to reference SQL. {original}/{len(tables)} pass original inputs and {robust}/{len(tables)} pass original inputs plus every synthetic control.**',
        'Every task has two identical queries except b04, which has three. Byte identity is a file comparison, not independent proof of financial correctness.',
        'Cases requiring no SQL repair under original inputs and all available controls: ' + (', '.join(no_repair) or 'none') + '.', '',
        'SQL-only diagnostics reuse frozen comparison functions, pristine databases and the existing isolated verifier. Claims, citations, evidence and whole-task completion are **unassessed**, with no gold answer.json or fabricated verdicts supplied. Synthetic controls establish behavior on those authored perturbations only.', '',
        '## Current table baseline', '',
        'The task column links the frozen task. Files are environment/starting_<table>.sql and solution/<table>.sql. Controls counts exclude original inputs. Failure names and scorer reasons are explicit.', '',
        '| Task | Table | Byte identical | Original | Controls passed | Failed controls |',
        '| --- | --- | --- | --- | --- | --- |']
    for key, result in results.items():
        for name, item in result['verdict']['details']['tables'].items():
            values = state(item)
            lines.append(f'| [{key}](../../datasets/workflow-v6/tasks/{key}/instruction.md) | {name} | {"yes" if result["byte_identical"][name] else "no"} | {values[0]} | {values[1]} | {values[2]} |')
    lines += ['', '## Retained model transitions', '',
        'Repair = incorrect to correct, Preservation = correct to correct, Regression = correct to incorrect, Unrepaired = incorrect to incorrect. Classify original-input correctness separately from correctness on original inputs plus every control. Each comparison uses one frozen task/scorer on both sides.',
        'Corrected workflow-v5 replays are separate from original workflow-v5 scores and are not workflow-v6 model results. Changes between scorer versions are scorer corrections, not model repairs. Original submissions, scores and correction receipts remain unchanged.', '',
        '| Attempt / scoring view | Table | Starting original / controls | Submitted original / controls | Original transition | All-input transition |',
        '| --- | --- | --- | --- | --- | --- |']
    counts = {}
    for dataset, key, attempt, path in entries:
        for view in (['original', 'corrected'] if dataset == 'workflow-v5' else ['original']):
            before_result = historical[dataset, key, view]
            if view == 'corrected' and before_result['reviewed_task_sha256'] != attempt['reviewed_task_sha256']:
                raise ValueError('transition_task_identity')
            verdict = attempt['verdict'] if view == 'corrected' else attempt['original_verdict']
            before = before_result['verdict']['details']['tables']
            after = verdict['details']['tables']
            if set(before) != set(after):
                raise ValueError('incomparable_table_sets')
            bucket = counts.setdefault(dataset + '/' + view, (Counter(), Counter()))
            for name in before:
                first, all_inputs = classify(before[name], after[name])
                bucket[0][first] += 1
                bucket[1][all_inputs] += 1
                b, a = before[name], after[name]
                start = f'{b["original"]} / {sum(b["controls"].values())}/{len(b["controls"])}'
                end = f'{a["original"]} / {sum(a["controls"].values())}/{len(a["controls"])}'
                lines.append(f'| {attempt["attempt_id"]} / {dataset} {view} | {name} | {start} | {end} | {first} | {all_inputs} |')
    lines += ['', '| Scoring view / scope | Repair | Preservation | Regression | Unrepaired |', '| --- | --- | --- | --- | --- |']
    for view, buckets in counts.items():
        for scope, bucket in zip(('original inputs', 'all inputs'), buckets):
            lines.append('| ' + view + ' / ' + scope + ' | ' + ' | '.join(str(bucket[name]) for name in ('Repair', 'Preservation', 'Regression', 'Unrepaired')) + ' |')
    lines += ['', 'The Microsoft basis-point query and Brale duplicate-export defect remain in the retained answers. The Block label correction changes acceptance without changing its SQL. The earlier workflow-v4 Brale delivery is reported under its original scorer.',
        'Incomplete deliveries, timeouts, interrupted and partial attempts lack comparable complete-delivery table verdicts and are unclassified here, rather than counted as incorrect SQL. See the [original development diagnostics](../local/workflow-development-diagnostics-1.json), [budget diagnostics](../local/workflow-development-budget-diagnostics-1.json), [hybrid diagnostics](../local/workflow-development-hybrid-diagnostics-1.json), [Qwen pilot](../local/workflow-qwen36-development-1.json), and [interrupted attempt](../local/workflow-qwen36-development-2-interrupted.json). Partial-query scoring and aggregation across unequal budgets are questions for deeper review.', '',
        '## Reproduction and provenance', '',
        'No inference or external service spending. Execution: Mac Pro, dedicated workpaperbench-local Linux guest. Containers use network none, read-only root, 384 MiB memory, one CPU, 32 PIDs, dropped capabilities, no-new-privileges and bounded tmpfs. Frozen SQL workers enforce the existing time, memory, read-only SQL and output limits. Every receipt passed all four existing isolation probes.',
        'Reproduce from the published revision with the documented [local verifier setup](../../docs/WORKFLOW.md):', '',
        '```sh', '.venv/bin/python scripts/starting_sql_baseline.py --output /tmp/starting-sql-baseline.md', '```', '',
        'Report implementation base: `' + subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() + '`.',
        'Generator SHA256: `' + digest(__file__) + '`.',
        'Verifier helper SHA256: `' + digest(ROOT / 'scripts/review_workflow.py') + '`.',
        'Container program SHA256: `' + hashlib.sha256(CONTAINER.encode()).hexdigest() + '`.',
        'Current manifest SHA256: `' + digest(ROOT / 'datasets/workflow-v6/manifest.json') + '`.',
        'Current scorer SHA256: `' + manifest['scorer_sha256'] + '`.',
        'Corrected replay SHA256: `' + digest(ROOT / 'reports/workflow-v5/corrected-replay.json') + '`.', '',
        'Historical catalogs: [workflow-v4](../../datasets/workflow-v4/manifest.json), [workflow-v5](../../datasets/workflow-v5/manifest.json). Corrected tasks are reconstructed by reviewed_task, preserving original inputs and starting SQL. [Corrected replay](../workflow-v5/corrected-replay.json) binds task hashes, submitted file hashes and original receipt hashes. The budget diagnostic binds the earlier receipt and SQL hashes. Task tree hashes below authenticate all starting/reference SQL, original and synthetic inputs, verifier code and gold expectations. Image IDs identify the executed verifier builds.', '',
        '| Baseline task / view | Task tree SHA256 | Verifier image |', '| --- | --- | --- |']
    lines += [f'| {name} | {task_hash} | {image} |' for name, task_hash, image in identities]
    lines += ['', 'These are bounded engineering diagnostics. They do not establish claim correctness, whole-task success, human agreement, independent domain validation or model performance on workflow-v6. The high starting-correct fraction and the no-repair case should inform the deeper methodology review without changing the tasks or grader in this pass.', '']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('\n'.join(lines))
    print(json.dumps({'byte_identical': same, 'tables': len(tables), 'original_correct': original,
                      'all_inputs_correct': robust, 'no_sql_repair': no_repair,
                      'transitions': {key: [dict(bucket) for bucket in value] for key, value in counts.items()}}))


if __name__ == '__main__':
    main()
