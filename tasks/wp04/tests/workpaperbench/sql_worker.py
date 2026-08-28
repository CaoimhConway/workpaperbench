"""Read one scalar query in a bounded, key-free process."""
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import time


SAFE_FUNCTIONS = {
    "sum", "total", "count", "min", "max", "avg", "round", "abs", "coalesce",
    "ifnull", "nullif", "lower", "upper", "length", "substr", "substring",
    "trim", "ltrim", "rtrim", "replace", "instr", "typeof", "iif", "like", "glob",
    "row_number", "rank", "dense_rank", "percent_rank", "cume_dist", "ntile",
    "lag", "lead", "first_value", "last_value", "nth_value",
}
DATE_FUNCTIONS = {"date", "time", "datetime", "julianday", "unixepoch", "strftime"}


def install_dates(connection):
    # Bound arguments, fixed function names and a separate in-memory connection.
    # Reject wall-clock/timezone inputs, including column values equal to "now".
    dates = sqlite3.connect(":memory:")
    def function(name):
        def call(*args):
            if len(args) < (2 if name == "strftime" else 1):
                raise ValueError("date_requires_explicit_input")
            if any(isinstance(a, (bytes, bytearray)) for a in args):
                raise ValueError("date_requires_text_or_numeric_input")
            forbidden = {"now", "localtime", "utc", "subsec", "subsecond"}
            if any(isinstance(a, str) and a.strip().lower() in forbidden for a in args):
                raise ValueError("nondeterministic_date")
            marks = ",".join("?" for _ in args)
            return dates.execute("SELECT " + name + "(" + marks + ")", args).fetchone()[0]
        return call
    for name in DATE_FUNCTIONS:
        connection.create_function(name, -1, function(name), deterministic=True)
    return dates


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
    dates = install_dates(connection)
    functions = SAFE_FUNCTIONS | DATE_FUNCTIONS

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
    if cursor.description is None or len(cursor.description) != 1 or cursor.description[0][0].lower() != "value":
        raise ValueError("scalar_column")
    rows = cursor.fetchmany(2)
    if len(rows) != 1:
        raise ValueError("scalar_rows")
    value = rows[0][0]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("finite_number")
    connection.close()
    dates.close()
    return value


if __name__ == "__main__":
    try:
        request = json.loads(sys.stdin.buffer.read(20000))
        print(json.dumps({"value": run(request["db"], request["sql"])}))
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__}))
        sys.exit(1)
