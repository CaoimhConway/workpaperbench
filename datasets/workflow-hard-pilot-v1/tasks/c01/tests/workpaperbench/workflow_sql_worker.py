"""Bounded read-only SQL table replay inside the isolated verifier."""
import json
import math
from pathlib import Path
import sqlite3
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))
from challenge_sql_worker import DATE_FUNCTIONS, SAFE_FUNCTIONS, install_dates


MAX_SQL_BYTES = 16384
MAX_REQUEST_BYTES = 131072


def read_request(stream):
    raw = stream.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        raise ValueError('request_size')
    return json.loads(raw)


def run(db, sql):
    if not isinstance(sql, str) or len(sql.encode()) > MAX_SQL_BYTES:
        raise ValueError('sql_size')
    if sys.platform != 'linux':
        raise ValueError('workflow_replay_requires_isolated_linux')
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    connection = sqlite3.connect(Path(db).resolve().as_uri() + '?mode=ro', uri=True)
    connection.enable_load_extension(False)
    connection.execute('PRAGMA query_only=ON')
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    dates = install_dates(connection)
    def authorize(action, a, b, database, trigger):
        if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE):
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ and database == 'main' and a in tables:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and (b or '').lower() in SAFE_FUNCTIONS | DATE_FUNCTIONS:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    connection.set_authorizer(authorize)
    deadline = time.monotonic() + 1.5
    connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
    cursor = connection.execute(sql)
    if cursor.description is None or not 1 <= len(cursor.description) <= 16:
        raise ValueError('table_columns')
    columns = [column[0] for column in cursor.description]
    if len(set(columns)) != len(columns):
        raise ValueError('duplicate_columns')
    rows = cursor.fetchmany(101)
    if len(rows) > 100:
        raise ValueError('table_rows')
    for row in rows:
        for value in row:
            if value is not None and (isinstance(value, bytes) or not isinstance(value, (str, int, float))):
                raise ValueError('table_cell_type')
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError('nonfinite_cell')
            if isinstance(value, str) and len(value.encode()) > 1024:
                raise ValueError('table_cell_size')
    result = {'columns': columns, 'rows': rows}
    if len(json.dumps(result, allow_nan=False).encode()) > 65536:
        raise ValueError('table_output_size')
    connection.close()
    dates.close()
    return result


if __name__ == '__main__':
    try:
        request = read_request(sys.stdin.buffer)
        print(json.dumps(run(request['db'], request['sql']), allow_nan=False))
    except Exception as error:
        print(json.dumps({'error': type(error).__name__}))
        sys.exit(1)
