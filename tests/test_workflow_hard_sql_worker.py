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
WORKER = ROOT / 'config/scorers/workflow_hard_sql_worker-1.0.0.py'
FROZEN = ROOT / 'config/scorers/workflow_sql_worker-1.2.1.py'
IMAGE = (ROOT / 'datasets/workflow-hard-eval-v1/tasks/b02/tests/Dockerfile').read_text().splitlines()[0].split()[1]

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
for name, sql in payload['queries'].items():
    start = time.monotonic()
    run = subprocess.run([sys.executable, '-I', '-S', str(root / 'worker.py')],
        input=json.dumps({'db': str(db), 'sql': sql}), text=True, capture_output=True,
        timeout=8, env={'PATH':'/usr/local/bin:/usr/bin:/bin'})
    results[name] = {'returncode':run.returncode, 'seconds':time.monotonic()-start,
                     'output':json.loads(run.stdout) if run.stdout else None}
print(json.dumps({'sqlite_version':sqlite3.sqlite_version, 'results':results,
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
    payload = {'files':{name:base64.b64encode(path.read_bytes()).decode() for name,path in files.items()},
               'queries':{**{name:sql for name,(sql,_) in ACCEPTED.items()}, **REJECTED}}
    command = ['docker', 'run', '--rm', '--network', 'none', '--read-only', '--memory', '384m',
               '--cpus', '1', '--pids-limit', '32', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,noexec,nosuid,size=4m',
               '-i', tag, 'python', '-I', '-S', '-c', CONTAINER]
    run = subprocess.run(command, input=json.dumps(payload), text=True, capture_output=True,
                         check=True, timeout=40)
    result = json.loads(run.stdout)
    assert result['sqlite_version'] == '3.40.1'
    assert result['database_unchanged'] and result['extra_database_absent']
    return result['results']


@pytest.mark.parametrize('name', ACCEPTED)
def test_equivalent_read_forms_pass(isolated_results, name):
    result = isolated_results[name]
    assert result['returncode'] == 0, result
    assert result['output'] == {'columns':['n'], 'rows':[[ACCEPTED[name][1]]]}, result


@pytest.mark.parametrize('name', REJECTED)
def test_access_and_resource_boundaries_remain(isolated_results, name):
    result = isolated_results[name]
    assert result['returncode'] != 0, result
    assert result['output'] is None or 'error' in result['output'], result
    assert result['seconds'] < 8, result


def test_frozen_baseline_and_non_authorization_behavior_unchanged():
    assert hashlib.sha256(FROZEN.read_bytes()).hexdigest() == '07a2d2203152982ac8ead066908f8030de05f108b28298241cfd33c3c7f51200'
    prior, current = FROZEN.read_text(), WORKER.read_text()
    marker = "    connection.execute('PRAGMA query_only=ON')"
    assert prior.split(marker)[0] == current.split(marker)[0]
    marker = '    connection.set_authorizer(authorize)'
    assert prior.split(marker)[1] == current.split(marker)[1]
