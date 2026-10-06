"""Bounded, content-free observation of native provider API retry events."""

import hashlib
import json
import math
import os
from pathlib import Path
import threading
import time


_MAX_EVENTS = 256
_MAX_BYTES = 65_536
_MAX_REQUESTS = 256
_lock = threading.RLock()
_events = 0
_request_attempts = {}


def _positive_counter(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1_000_000_000:
        return None
    return value


def _timestamp(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and 0 < number < 10_000_000_000 else None


def _opaque_id(value):
    if not isinstance(value, str) or not value or len(value) > 256:
        return None
    return hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()


def _ledger_path():
    value = os.environ.get("WPB_NATIVE_RETRY_LEDGER", "")
    if not value:
        return None
    path = Path(value)
    if (path.as_posix() != "/logs/agent/native-api-observer.jsonl"
            or any(parent.is_symlink() for parent in (path.parent, path.parent.parent))):
        return None
    return path


def _record(event, **fields):
    global _events
    path = _ledger_path()
    if path is None:
        return
    with _lock:
        if _events >= _MAX_EVENTS:
            return
        try:
            if path.is_symlink():
                return
            current_size = path.stat().st_size if path.exists() else 0
            if current_size >= _MAX_BYTES:
                return
            row = {"event": event, "observed_at": time.time(), **fields}
            encoded = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
            if current_size + len(encoded) > _MAX_BYTES:
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("ab") as stream:
                stream.write(encoded)
            _events += 1
        except (OSError, ValueError, TypeError):
            return


def _common(kwargs):
    return {
        "request_id": _opaque_id(kwargs.get("api_request_id")),
        "api_call_count": _positive_counter(kwargs.get("api_call_count")),
        "retry_count": _positive_counter(kwargs.get("retry_count")),
        "max_retries": _positive_counter(kwargs.get("max_retries")),
        "started_at": _timestamp(kwargs.get("started_at")),
    }


def _pre_api_request(**kwargs):
    common = _common(kwargs)
    request_id = common["request_id"]
    with _lock:
        ordinal = None
        if request_id is not None:
            if request_id in _request_attempts:
                _request_attempts[request_id] += 1
            elif len(_request_attempts) < _MAX_REQUESTS:
                _request_attempts[request_id] = 1
            ordinal = _request_attempts.get(request_id)
        _record("pre_api_request", **common, attempt_ordinal=ordinal)


def _post_api_request(**kwargs):
    common = _common(kwargs)
    common["ended_at"] = _timestamp(kwargs.get("ended_at"))
    _record("post_api_request", **common)


def _api_request_error(**kwargs):
    common = _common(kwargs)
    common["ended_at"] = _timestamp(kwargs.get("ended_at"))
    status = kwargs.get("status_code")
    common["http_status"] = status if isinstance(status, int) and not isinstance(status, bool) and 100 <= status <= 599 else None
    retryable = kwargs.get("retryable")
    common["retryable"] = retryable if isinstance(retryable, bool) else None
    _record("api_request_error", **common)


def register(ctx):
    ctx.register_hook("pre_api_request", _pre_api_request)
    ctx.register_hook("post_api_request", _post_api_request)
    ctx.register_hook("api_request_error", _api_request_error)
    _record("observer_registered")
