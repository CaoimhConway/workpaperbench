"""Status observation for local, non-restarting launchd pilot supervisors."""

import json
import re
import subprocess
import time
from datetime import datetime, timezone


def launcher_fields(observation, target, plist):
    """Read only fields belonging to this unique local launchd registration."""
    lines = observation.stdout.splitlines()
    if observation.returncode or not lines or lines[0] != target + ' = {':
        return {}
    fields = {}
    for line in lines[1:]:
        match = re.fullmatch(r'\t([^\t=]+) = ([^\n]+)', line)
        if match:
            key, value = match.groups()
            if key in fields:
                return {}
            fields[key] = value
    return fields if fields.get('path') == str(plist) else {}


def launcher_status(observation, target, plist):
    """Require the current one-shot job and consistent top-level process fields."""
    fields = launcher_fields(observation, target, plist)
    if fields.get('runs') != '1':
        return 'unknown'
    state, active, pid = (fields.get(k) for k in ('state', 'active count', 'pid'))
    has_pid = pid is not None and re.fullmatch(r'[1-9][0-9]*', pid) is not None
    if active == '1' and has_pid:
        # A previous exit field does not describe the active launch.
        if state == 'xpcproxy':
            return 'startup'
        if state == 'running':
            return 'running'
    if state == 'not running' and active == '0' and pid is None:
        if re.fullmatch(r'-?[0-9]+', fields.get('last exit code', '')):
            return 'terminated'
    return 'unknown'


def current_terminal_record(root, reserved_at):
    """The result and launch marker must belong to this reserved attempt."""
    try:
        start = json.loads((root / 'launch-state.json').read_text())
        result = json.loads((root / 'launch-result.json').read_text())
        began = datetime.fromisoformat(start['started_at'])
        reserved = datetime.fromisoformat(reserved_at)
        ended = datetime.fromisoformat(result['finished_at'])
        valid = (began >= reserved and ended >= began
                 and result['started_at'] == start['started_at']
                 and result['status'] == 'native_process_finished'
                 and start['one_attempt_only'] is True
                 and result['one_attempt_only'] is True
                 and type(result['exit_code']) is int)
        return result if valid else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def read_launchd(target):
    try:
        return subprocess.run(['launchctl', 'print', target], capture_output=True,
                              text=True, timeout=10)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(['launchctl', 'print', target], -1,
                                           '', 'launchctl status query timed out')


def wait_for_launcher(root, target, reserved_at, *, poll_seconds=15,
                      status_grace_seconds=60, query=None, sleep=None, clock=None):
    """Observe only. Uncertainty stops collection, never submits another launch.

    Native execution deadlines remain unchanged. The grace bounds startup or
    unavailable status, rather than extending any candidate execution budget.
    """
    query = query or read_launchd
    sleep = sleep or time.sleep
    clock = clock or time.monotonic
    unresolved_since = clock()
    previous_exit = None
    while True:
        terminal = current_terminal_record(root, reserved_at)
        if terminal is not None:
            return terminal
        observed = query(target)
        status = launcher_status(observed, target, root / 'supervisor.plist')
        with (root / 'supervision-observations.jsonl').open('a') as stream:
            stream.write(json.dumps({'observed_at': datetime.now(timezone.utc).isoformat(),
                                    'classification': status,
                                    'returncode': observed.returncode,
                                    'stdout': observed.stdout, 'stderr': observed.stderr}) + '\n')
        # Publication can race the status query, including its apparent exit.
        terminal = current_terminal_record(root, reserved_at)
        if terminal is not None:
            return terminal
        if status == 'terminated' and previous_exit == observed.stdout:
            (root / 'supervision-early-exit.log').write_text(observed.stdout + observed.stderr)
            raise RuntimeError('launcher_exited_without_final_record')
        previous_exit = observed.stdout if status == 'terminated' else None
        if status == 'running':
            unresolved_since = None
        elif unresolved_since is None:
            unresolved_since = clock()
        if unresolved_since is not None and clock() - unresolved_since >= status_grace_seconds:
            raise RuntimeError('launcher_status_unresolved')
        sleep(poll_seconds)
