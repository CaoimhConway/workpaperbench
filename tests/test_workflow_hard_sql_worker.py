"""Trusted SQL boundary fixtures replayed only in the isolated Linux image."""
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / 'config/scorers/workflow_hard_sql_worker-1.0.1.py'
PRIOR = ROOT / 'config/scorers/workflow_hard_sql_worker-1.0.0.py'
FROZEN = ROOT / 'config/scorers/workflow_sql_worker-1.2.1.py'
B02 = ROOT / 'datasets/workflow-hard-eval-v1/tasks/b02/tests'
IMAGE = (B02 / 'Dockerfile').read_text().splitlines()[0].split()[1]
GROUPED_SQL = ROOT / 'tests/fixtures/workflow_hard_grouped_sale_allocations.sql'
GOLD = json.loads((B02 / 'gold.json').read_text())
GROUPED_CASES = {'original':('data.sqlite', GOLD['tables']['sale_allocations']['rows'])}
GROUPED_CASES.update({c['name']:(c['database'],c['tables']['sale_allocations']) for c in GOLD['controls']})

ACCEPTED = {
    'count_star': ('SELECT COUNT(*) AS n FROM terms', 3),
    'count_constant': ('SELECT COUNT(1) AS n FROM terms', 3),
    'count_column': ('SELECT COUNT(series) AS n FROM terms', 2),
    'case_table': ('SELECT COUNT(*) AS n FROM TERMS', 3),
    'case_schema': ('SELECT COUNT(*) AS n FROM MAIN.TeRmS', 3),
    'exists': ('SELECT EXISTS(SELECT 1 FROM terms) AS n', 1),
    'constant_projection': ('SELECT 1 AS n FROM terms LIMIT 1', 1),
    'unused_join': ('SELECT SUM(a.qty) AS n FROM terms a CROSS JOIN terms b', 18),
    'ordinary_cte': ('WITH q AS (SELECT series FROM terms) SELECT COUNT(*) AS n FROM q', 3),
    'materialized_cte': ('WITH q AS MATERIALIZED (SELECT series FROM terms) SELECT COUNT(*) AS n FROM q', 3),
    'constant_cte': ('WITH q AS MATERIALIZED (SELECT 1 AS x UNION ALL SELECT 2) SELECT COUNT(*) AS n FROM q', 2),
    'recursive_cte': ('WITH RECURSIVE q(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM q WHERE x<3) SELECT COUNT(*) AS n FROM q', 3),
}

REJECTED = {
    'schema_columns': 'SELECT name FROM sqlite_schema',
    'view_columns': 'SELECT series FROM allowed_view',
    'view_schema': 'SELECT COUNT(*) AS n FROM schema_view',
    'shadow_view': 'WITH allowed_view AS MATERIALIZED (SELECT 1 AS x) SELECT COUNT(*) AS n FROM allowed_view',
    'cte_hides_schema': 'WITH q AS MATERIALIZED (SELECT name FROM sqlite_schema) SELECT COUNT(*) AS n FROM q',
    'pragma_database': 'SELECT COUNT(*) AS n FROM pragma_database_list',
    'pragma_info': "SELECT COUNT(*) AS n FROM pragma_table_info('terms')",
    'json_each': "SELECT COUNT(*) AS n FROM json_each('[1,2]')",
    'json_tree': "SELECT COUNT(*) AS n FROM JSON_TREE('[1,2]')",
    'dbstat': 'SELECT COUNT(*) AS n FROM dbstat',
    'module_shadow': 'WITH json_each AS MATERIALIZED (SELECT 1 AS x) SELECT COUNT(*) AS n FROM json_each',
    'readfile': "SELECT readfile('/tmp/worker-test/sentinel.txt') AS n",
    'load_extension': "SELECT load_extension('/tmp/missing') AS n",
    'nondeterministic_function': 'SELECT random() AS n',
    'wall_clock': "SELECT datetime('now') AS n",
    'attach': "ATTACH DATABASE '/tmp/other.sqlite' AS other",
    'temp_create': 'CREATE TEMP TABLE hidden(x)',
    'write': 'UPDATE terms SET qty=0',
    'pragma': 'PRAGMA database_list',
    'multi_statement': 'SELECT 1 AS n; SELECT 2 AS n',
    'oversized_sql': 'SELECT 1 AS n /*' + 'x' * 16384 + '*/',
    'columns': 'SELECT ' + ','.join('1 AS c' + str(i) for i in range(17)),
    'rows': 'WITH RECURSIVE q(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM q WHERE x<101) SELECT x FROM q',
    'cell_size': "SELECT '" + 'x' * 1025 + "' AS n",
    'nonfinite': 'SELECT 1e999 AS n',
    'blob': "SELECT x'00' AS n",
    'unbounded_recursion': 'WITH RECURSIVE q(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM q) SELECT SUM(x) AS n FROM q',
}
for alias in ['sqlite_master', 'sqlite_schema', 'sqlite_temp_master', 'sqlite_temp_schema']:
    REJECTED['count_' + alias] = 'SELECT COUNT(*) AS n FROM ' + alias.upper()
    REJECTED['shadow_' + alias] = 'WITH ' + alias + ' AS MATERIALIZED (SELECT 1 AS x) SELECT COUNT(*) AS n FROM ' + alias


CONTAINER = r'''
import base64, hashlib, json, pathlib, sqlite3, subprocess, sys, time
payload = json.load(sys.stdin)
root = pathlib.Path('/tmp/worker-test')
root.mkdir()
for name, value in payload['files'].items():
    (root / name).write_bytes(base64.b64decode(value))
(root / 'sentinel.txt').write_text('not query data')
db = root / 'data.sqlite'
with sqlite3.connect(db) as connection:
    connection.execute('CREATE TABLE terms(series TEXT, qty INTEGER)')
    connection.executemany('INSERT INTO terms VALUES (?,?)', [('A',1),('B',2),(None,3)])
    connection.execute('CREATE VIEW allowed_view AS SELECT series FROM terms')
    connection.execute('CREATE VIEW schema_view AS SELECT name FROM sqlite_schema')
before = hashlib.sha256(db.read_bytes()).hexdigest()
results = {}
def replay(sql, database):
    start = time.monotonic()
    run = subprocess.run([sys.executable, '-I', '-S', str(root / 'worker.py')],
        input=json.dumps({'db': str(database), 'sql': sql}), text=True, capture_output=True,
        timeout=8, env={'PATH':'/usr/local/bin:/usr/bin:/bin'})
    return {'returncode':run.returncode, 'seconds':time.monotonic()-start,
            'output':json.loads(run.stdout) if run.stdout else None}
for name, sql in payload['queries'].items():
    results[name] = replay(sql, db)
grouped = {}
for name, filename in payload['grouped_databases'].items():
    database = root / filename
    original = hashlib.sha256(database.read_bytes()).hexdigest()
    grouped[name] = replay(payload['grouped_sql'], database)
    assert original == hashlib.sha256(database.read_bytes()).hexdigest()
print(json.dumps({'sqlite_version':sqlite3.sqlite_version, 'results':results,
                  'grouped':grouped,
                  'database_unchanged':before == hashlib.sha256(db.read_bytes()).hexdigest(),
                  'extra_database_absent':not pathlib.Path('/tmp/other.sqlite').exists()}))
'''


@pytest.fixture(scope='module')
def isolated_results():
    if sys.platform != 'linux' or shutil.which('docker') is None:
        pytest.skip('Worker execution requires the Linux Docker guest')
    tag = 'wpb-hard-worker-test-' + hashlib.sha256(IMAGE.encode()).hexdigest()[:16]
    with tempfile.TemporaryDirectory(prefix='wpb-worker-image-') as context:
        (Path(context) / 'Dockerfile').write_text('FROM ' + IMAGE + '\n')
        subprocess.run(['docker', 'build', '--network', 'none', '-t', tag, context],
                       check=True, capture_output=True, timeout=180)
    files = {'worker.py':WORKER, 'challenge_sql_worker.py':ROOT / 'workpaperbench/challenge_sql_worker.py'}
    files.update({'b02-'+filename:B02 / filename for filename,_ in GROUPED_CASES.values()})
    payload = {'files':{name:base64.b64encode(path.read_bytes()).decode() for name,path in files.items()},
               'queries':{**{name:sql for name,(sql,_) in ACCEPTED.items()}, **REJECTED},
               'grouped_sql':GROUPED_SQL.read_text(),
               'grouped_databases':{name:'b02-'+filename for name,(filename,_) in GROUPED_CASES.items()}}
    command = ['docker', 'run', '--rm', '--network', 'none', '--read-only', '--memory', '384m',
               '--cpus', '1', '--pids-limit', '32', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,noexec,nosuid,size=4m',
               '-i', tag, 'python', '-I', '-S', '-c', CONTAINER]
    run = subprocess.run(command, input=json.dumps(payload), text=True, capture_output=True,
                         check=True, timeout=40)
    result = json.loads(run.stdout)
    assert result['sqlite_version'] == '3.40.1'
    assert result['database_unchanged'] and result['extra_database_absent']
    return result


@pytest.mark.parametrize('name', ACCEPTED)
def test_equivalent_read_forms_pass(isolated_results, name):
    result = isolated_results['results'][name]
    assert result['returncode'] == 0, result
    assert result['output'] == {'columns':['n'], 'rows':[[ACCEPTED[name][1]]]}, result


@pytest.mark.parametrize('name', REJECTED)
def test_access_and_resource_boundaries_remain(isolated_results, name):
    result = isolated_results['results'][name]
    assert result['returncode'] != 0, result
    assert result['output'] is None or 'error' in result['output'], result
    assert result['seconds'] < 8, result


@pytest.mark.parametrize('name', GROUPED_CASES)
def test_grouped_alternative_matches_frozen_gold(isolated_results, name):
    result = isolated_results['grouped'][name]
    assert result['returncode'] == 0, result
    output = result['output']
    columns = GOLD['tables']['sale_allocations']['columns']
    assert set(output['columns']) == set(columns)
    actual = sorted([[row[output['columns'].index(c)] for c in columns] for row in output['rows']])
    expected = sorted(GROUPED_CASES[name][1])
    for row, wanted in zip(actual, expected, strict=True):
        for column, got, target in zip(columns.values(), row, wanted, strict=True):
            assert got == target if column['type'] == 'text' else got == pytest.approx(target, rel=0, abs=column['tolerance'])


def test_frozen_baseline_and_non_authorization_behavior_unchanged():
    assert hashlib.sha256(FROZEN.read_bytes()).hexdigest() == '07a2d2203152982ac8ead066908f8030de05f108b28298241cfd33c3c7f51200'
    prior, current = FROZEN.read_text(), WORKER.read_text()
    marker = "    connection.execute('PRAGMA query_only=ON')"
    assert prior.split(marker)[0] == current.split(marker)[0]
    marker = '    connection.set_authorizer(authorize)'
    assert prior.split(marker)[1] == current.split(marker)[1]
    assert hashlib.sha256(PRIOR.read_bytes()).hexdigest() == '4103f82f9b3af6fce87f0db2235f581bceee7cabc0ab88822280950e914ec7e4'
    marker = "    connection.execute('PRAGMA query_only=ON')\n"
    assert current == PRIOR.read_text().replace(marker, marker + "    connection.execute('PRAGMA temp_store=MEMORY')\n")
    assert hashlib.sha256(GROUPED_SQL.read_bytes()).hexdigest() == 'ee38fb12c920ada9753557746c345b7dbaa0b60aa3213ce7006fa23bf906af3f'
