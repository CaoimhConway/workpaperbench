"""Read one scalar query in a bounded, key-free process."""
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import time


def run(db, sql):
    if not isinstance(sql, str) or len(sql.encode()) > 16384:
        raise ValueError("sql_size")
    if sys.platform == "linux":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    connection = sqlite3.connect(Path(db).resolve().as_uri() + "?mode=ro", uri=True)
    if hasattr(connection, "enable_load_extension"):
        connection.enable_load_extension(False)
    connection.execute("PRAGMA query_only=ON")
    tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    functions = {"sum", "total", "count", "min", "max", "avg", "round", "abs", "coalesce", "ifnull", "nullif"}

    def authorize(action, a, b, database, trigger):
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ and database == "main" and a in tables:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and (b or "").lower() in functions:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_RECURSIVE:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    connection.set_authorizer(authorize)
    deadline = time.monotonic() + 1.5
    connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
    cursor = connection.execute(sql)
    if cursor.description is None or len(cursor.description) != 1 or cursor.description[0][0] != "value":
        raise ValueError("scalar_column")
    rows = cursor.fetchmany(2)
    if len(rows) != 1:
        raise ValueError("scalar_rows")
    value = rows[0][0]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("finite_number")
    connection.close()
    return value


if __name__ == "__main__":
    try:
        request = json.loads(sys.stdin.buffer.read(20000))
        print(json.dumps({"value": run(request["db"], request["sql"])}))
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__}))
        sys.exit(1)
