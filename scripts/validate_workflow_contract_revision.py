"""Validate calculation conventions and SQL transport in isolated Linux verifiers."""
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

DATASET = 'workflow-v11'
CASES = {
    'c01': ('equivalent_arithmetic', 'unicode_comment', 'maximum_escaped_comment',
            'outside_numeric_tolerance', 'oversized_sql'),
    'b06': ('sufficient_single_citation', 'unknown_citation', 'opposite_residuals'),
    'b02': ('reconstructed_stock_bridge',),
}
DOCKER_LIMITS = ['--rm', '--network', 'none', '--read-only', '--memory', '384m',
    '--cpus', '1', '--pids-limit', '32', '--cap-drop', 'ALL',
    '--security-opt', 'no-new-privileges',
    '--tmpfs', '/logs:rw,noexec,nosuid,size=4m', '--tmpfs', '/tmp:rw,noexec,nosuid,size=4m']
WORKER_PROBES = '''import hashlib,io,json,os,pathlib,runpy,socket,subprocess,sys
worker='/tests/workpaperbench/workflow_sql_worker.py'
namespace=runpy.run_path(worker,run_name='worker_probe')
sql='SELECT 1 AS value /*'+'é'*6000+'*/'
requests=[('oversized_request',b' '*(131072+1),1,{'error':'ValueError'}),
 ('malformed_json',b'{"sql":',1,{'error':'JSONDecodeError'}),
 ('unicode_query',json.dumps({'sql':sql,'db':'/tests/data.sqlite'}).encode(),0,
  {'columns':['value'],'rows':[[1]]})]
outcomes=[]
for name,raw,code,expected in requests:
 result=subprocess.run([sys.executable,'-I','-S',worker],input=raw,capture_output=True,
  timeout=5,cwd='/tests/workpaperbench',env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
 try:
  parsed=json.loads(result.stdout)
 except (ValueError,UnicodeError):
  parsed=None
 reason=None
 if name=='oversized_request':
  try:
   namespace['read_request'](io.BytesIO(raw))
  except ValueError as error:
   reason=str(error)
 passed=result.returncode==code and parsed==expected
 if name=='oversized_request':
  passed=passed and reason=='request_size' and len(raw)==131073
 if name=='unicode_query':
  passed=passed and len(sql.encode())<=16384 and len(raw)>20000
 outcomes.append({'case':name,'request_bytes':len(raw),
  'request_sha256':hashlib.sha256(raw).hexdigest(),'expected_returncode':code,
  'expected_output':expected,'returncode':result.returncode,'output':parsed,
  'raw_stdout':result.stdout.decode(),'raw_stderr':result.stderr.decode(),
  'oversized_rejection_reason':reason,'expectation_passed':passed})
network_blocked=False
try:
 with socket.create_connection(('1.1.1.1',443),timeout=2):
  pass
except OSError:
 network_blocked=True
isolation={'network_namespace_none':[name for _,name in socket.if_nameindex()]==['lo'],
 'network_probe_blocked':network_blocked,
 'no_inference_key':not any(k.endswith('API_KEY') or k in ('GITHUB_TOKEN','GH_TOKEN') for k in os.environ),
 'no_docker_socket':not pathlib.Path('/var/run/docker.sock').exists()}
print(json.dumps({'probes':outcomes,'isolation':isolation}))
'''


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('validation_sql_anchor_changed:' + before)
    return text.replace(before, after, 1)


def padded_comment(sql, length, pattern='"\\'):
    prefix, suffix = '\n/*', '*/\n'
    remaining = length - len((sql + prefix + suffix).encode())
    if remaining < 0 or not pattern.isascii():
        raise ValueError('validation_padding_length')
    padding = (pattern * (remaining // len(pattern) + 1))[:remaining]
    result = sql + prefix + padding + suffix
    if len(result.encode()) != length:
        raise ValueError('validation_padding_mismatch')
    return result


def artifacts(task, case):
    answer = json.loads((task / 'tests/reference.json').read_text())
    files = {entry['file']: (task / 'solution' / entry['file']).read_text()
             for entry in answer['tables']}
    if case in CASES['c01']:
        name = 'reconciliation.sql'
        before = 'n.revenue-o.revenue revenue_change_usd_thousand'
        if case == 'equivalent_arithmetic':
            files[name] = replace_once(files[name], before,
                '(n.revenue/1000.0-o.revenue/1000.0)*1000.0 revenue_change_usd_thousand')
        elif case == 'unicode_comment':
            files[name] += '\n/*' + 'é' * 6000 + '*/\n'
        elif case == 'maximum_escaped_comment':
            files[name] = padded_comment(files[name], 16384)
        elif case == 'outside_numeric_tolerance':
            files[name] = replace_once(files[name], before,
                '(n.revenue-o.revenue)+0.001 revenue_change_usd_thousand')
        elif case == 'oversized_sql':
            files[name] = padded_comment(files[name], 16385, 'x')
    elif case in ('sufficient_single_citation', 'unknown_citation'):
        entry = next(c for c in answer['claims'] if c['id'] == 'claim_1')
        entry['evidence'] = ['b06:s01'] if case == 'sufficient_single_citation' else ['b06:s01', 'b06:s99']
    elif case == 'opposite_residuals':
        name = 'corporate_bridge.sql'
        for before, after in (
            ('e+p.corporate_cost_usd_million-p.adjusted_ebitda_usd_million ebitda_residual_usd_million',
             'p.adjusted_ebitda_usd_million-(e+p.corporate_cost_usd_million) ebitda_residual_usd_million'),
            ('b-p.bookings_usd_million bookings_residual_usd_million',
             'p.bookings_usd_million-b bookings_residual_usd_million'),
            ('r-p.revenue_usd_million revenue_residual_usd_million',
             'p.revenue_usd_million-r revenue_residual_usd_million')):
            files[name] = replace_once(files[name], before, after)
    elif case == 'reconstructed_stock_bridge':
        name = 'stock_bridge.sql'
        files[name] = files[name].replace('treasury_fair_value_usd', 'holdings_fair_value_usd')
        files[name] = files[name].replace('reported_assets_usd', 'reconstructed_assets_usd')
        files[name] = replace_once(files[name], 'FROM reserve_observations p JOIN reserve_observations c ON',
                                  'FROM reconstructed p JOIN reconstructed c ON')
        files[name] = ('WITH holdings AS (SELECT DISTINCT * FROM treasury_holdings),\n'
            'treasury AS (SELECT economic_date,SUM(fair_value_usd) fv FROM holdings GROUP BY economic_date),\n'
            'reconstructed AS (SELECT o.*,t.fv holdings_fair_value_usd,\n'
            'o.cash_usd+o.repo_fair_value_usd+t.fv reconstructed_assets_usd\n'
            'FROM reserve_observations o JOIN treasury t USING(economic_date))\n' + files[name])
    else:
        raise ValueError('unknown_validation_case')
    files['answer.json'] = json.dumps(answer, indent=2) + '\n'
    return {name: text.encode() for name, text in files.items()}


def expectation(case):
    checks = dict.fromkeys(('financial_answer', 'numerical_tables', 'claim_verdicts',
                           'evidence', 'robustness', 'delivery'), True)
    if case == 'outside_numeric_tolerance':
        checks.update(financial_answer=False, numerical_tables=False, robustness=False)
    elif case == 'oversized_sql':
        checks = dict.fromkeys(checks)
        checks['delivery'] = False
    elif case == 'unknown_citation':
        checks['evidence'] = False
    elif case in ('opposite_residuals', 'reconstructed_stock_bridge'):
        checks['robustness'] = False
    return checks


def validate_verdict(verdict, case):
    if (verdict.get('scorer_version') != 'workflow-1.2.1'
            or verdict.get('checks') != expectation(case)
            or not verdict.get('isolation') or not all(verdict['isolation'].values())):
        raise ValueError('unexpected_contract_verdict')
    complete = all(value is True for value in expectation(case).values())
    if verdict.get('complete') is not complete:
        raise ValueError('unexpected_contract_completion')
    if case in ('opposite_residuals', 'reconstructed_stock_bridge'):
        target = 'corporate_bridge' if case == 'opposite_residuals' else 'stock_bridge'
        for name, details in verdict['details']['tables'].items():
            if details['original'] is not True:
                raise ValueError('alternative_changed_original_numbers')
            for control, passed in details['controls'].items():
                expected = not (name == target and control == 'independent_disclosure_discrepancy')
                if passed is not expected:
                    raise ValueError('unexpected_alternative_control:' + name + ':' + control)
    if case == 'outside_numeric_tolerance':
        for name, details in verdict['details']['tables'].items():
            expected = name != 'reconciliation'
            if details['original'] is not expected or any(value is not expected for value in details['controls'].values()):
                raise ValueError('unexpected_numeric_tolerance_diagnostic:' + name)


def execute_container(image_id, code, payload=None):
    return subprocess.run(['docker', 'run', *DOCKER_LIMITS, '-i', image_id, 'python', '-c', code],
                          input=payload, capture_output=True, timeout=90)


def validate(output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('contract_validation_report_already_exists')
    if platform.system() != 'Linux':
        raise ValueError('contract_validation_requires_linux_docker_controller')
    manifest = load(ROOT, DATASET)
    selected = {key: load(ROOT, DATASET, key) for key in CASES}
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {'validation_id': DATASET + '-contract-1', 'status': 'running',
        'manifest_id': manifest['manifest_id'],
        'manifest_sha256': digest((ROOT / 'datasets' / DATASET / 'manifest.json').read_bytes()),
        'scorer_version': manifest['scorer_version'], 'scorer_sha256': manifest['scorer_sha256'],
        'sql_worker_sha256': manifest['sql_worker_sha256'],
        'validator_sha256': digest(Path(__file__).read_bytes()),
        'verifier_build_sha256': digest(VERIFIER_BUILD.encode()),
        'verifier_controller_sha256': digest(CONTAINER.encode()),
        'inference': False, 'external_service_spend_usd': 0,
        'scope': 'Authored calculation, evidence and delivery cases, not model performance',
        'container_limits': DOCKER_LIMITS, 'cases': [], 'worker_probes': None, 'error': None}

    def save():
        output.write_text(json.dumps(report, indent=2) + '\n')

    with output.open('x') as stream:
        stream.write(json.dumps(report, indent=2) + '\n')
    (ROOT / '.local').mkdir(exist_ok=True)
    try:
        with (ROOT / '.local/local-command.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            subprocess.run(['docker', 'info'], check=True, stdout=subprocess.DEVNULL, timeout=30)
            images = {}
            for key, (_, spec, task) in selected.items():
                tag = 'wpb-contract-' + spec['task_sha256'][:16]
                subprocess.run([sys.executable, '-c', VERIFIER_BUILD, str(task / 'tests'), tag],
                               check=True, capture_output=True, timeout=300)
                image_id = subprocess.check_output(['docker', 'image', 'inspect', '--format={{.Id}}', tag],
                                                   timeout=30, text=True).strip()
                images[key] = image_id
                for case in CASES[key]:
                    files = artifacts(task, case)
                    sql_limits = {name: {'sql_utf8_bytes': len(raw),
                        'escaped_request_bytes': len(json.dumps({'sql': raw.decode(), 'db': '/tests/data.sqlite'}).encode())}
                        for name, raw in files.items() if name.endswith('.sql')}
                    if case in ('unicode_comment', 'maximum_escaped_comment'):
                        measured = sql_limits['reconciliation.sql']
                        if measured['sql_utf8_bytes'] > 16384 or measured['escaped_request_bytes'] <= 20000:
                            raise ValueError('escaped_request_counterexample_changed')
                    payload = json.dumps({name: base64.b64encode(raw).decode() for name, raw in files.items()}).encode()
                    result = execute_container(image_id, CONTAINER, payload)
                    row = {'task': key, 'task_sha256': spec['task_sha256'], 'case': case,
                        'image_id': image_id, 'files_sha256': {name: digest(raw) for name, raw in files.items()},
                        'sql_limits': sql_limits, 'expected_checks': expectation(case),
                        'returncode': result.returncode, 'raw_stdout': result.stdout.decode(),
                        'raw_stderr': result.stderr.decode(), 'verdict': None,
                        'expectation_passed': False, 'failure': None}
                    report['cases'].append(row)
                    try:
                        row['verdict'] = json.loads(result.stdout)
                        if result.returncode:
                            raise ValueError('isolated_verifier_failed')
                        validate_verdict(row['verdict'], case)
                        row['expectation_passed'] = True
                    except (ValueError, KeyError, TypeError) as error:
                        row['failure'] = type(error).__name__ + ':' + str(error)
                    save()
                    print(key, case, 'passed' if row['expectation_passed'] else 'FAILED', flush=True)
            result = execute_container(images['c01'], WORKER_PROBES)
            probes = {'image_id': images['c01'], 'returncode': result.returncode,
                'raw_stdout': result.stdout.decode(), 'raw_stderr': result.stderr.decode(),
                'result': None, 'expectation_passed': False}
            report['worker_probes'] = probes
            try:
                probes['result'] = json.loads(result.stdout)
                expected_names = ['oversized_request', 'malformed_json', 'unicode_query']
                probes['expectation_passed'] = (result.returncode == 0
                    and [r['case'] for r in probes['result']['probes']] == expected_names
                    and all(r['expectation_passed'] for r in probes['result']['probes'])
                    and bool(probes['result']['isolation']) and all(probes['result']['isolation'].values()))
            except (ValueError, KeyError, TypeError):
                pass
            for key, (_, spec, _) in selected.items():
                current, current_spec, _ = load(ROOT, DATASET, key)
                if current['manifest_id'] != manifest['manifest_id'] or current_spec != spec:
                    raise ValueError('contract_validation_inputs_changed')
            expected_cases = {(key, case) for key, cases in CASES.items() for case in cases}
            if ({(row['task'], row['case']) for row in report['cases']} != expected_cases
                    or len(report['cases']) != len(expected_cases)
                    or not all(row['expectation_passed'] for row in report['cases'])
                    or not probes['expectation_passed']):
                raise ValueError('contract_validation_expectations_failed')
            report['status'] = 'passed'
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        report['status'] = 'failed'
        report['error'] = type(error).__name__ + ':' + str(error)[:1000]
        raise
    finally:
        save()
    print('Contract validation passed: nine workpapers and three worker probes.')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    validate(parser.parse_args().output)
