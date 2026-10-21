import importlib.util
import io
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'workpaperbench.transport_revision', ROOT / 'config/scorers/workflow_sql_worker-1.2.1.py')
WORKER = importlib.util.module_from_spec(SPEC)
original_path = list(sys.path)
try:
    sys.path.insert(0, str(ROOT / 'workpaperbench'))
    SPEC.loader.exec_module(WORKER)
finally:
    sys.path[:] = original_path


@pytest.mark.parametrize('comment', ['é' * 6000, '"' * 16000, '\\' * 16000, '\x01' * 16000])
def test_permitted_sql_survives_json_escaping(comment):
    sql = 'SELECT 1 AS value /*' + comment + '*/'
    assert len(sql.encode()) <= WORKER.MAX_SQL_BYTES
    request = {'sql': sql, 'db': '/tests/data.sqlite'}
    raw = json.dumps(request).encode()
    assert len(raw) > 20000
    assert WORKER.read_request(io.BytesIO(raw)) == request


def test_maximum_sql_and_escaped_database_path_fit_the_envelope():
    sql = '\x01' * WORKER.MAX_SQL_BYTES
    request = {'sql': sql, 'db': '/' + '\x01' * 4095}
    raw = json.dumps(request).encode()
    assert len(raw) < WORKER.MAX_REQUEST_BYTES
    assert WORKER.read_request(io.BytesIO(raw)) == request


def test_oversized_request_is_rejected_explicitly():
    class Bounded(io.BytesIO):
        def read(self, size=-1):
            assert size == WORKER.MAX_REQUEST_BYTES + 1
            return super().read(size)

    with pytest.raises(ValueError, match='request_size'):
        WORKER.read_request(Bounded(b' ' * (WORKER.MAX_REQUEST_BYTES + 1)))


def test_malformed_json_is_not_misreported_as_a_size_error():
    with pytest.raises(json.JSONDecodeError):
        WORKER.read_request(io.BytesIO(b'{"sql":'))


@pytest.mark.parametrize('sql', ['x' * 16385, 'é' * 8193])
def test_decoded_sql_limit_stays_16384_utf8_bytes(sql):
    with pytest.raises(ValueError, match='sql_size'):
        WORKER.run('/unused', sql)
