"""Offline launchd observations, using the captured startup field relationships."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from macos_supervision import current_terminal_record, launcher_status, read_launchd, wait_for_launcher

TARGET = 'gui/501/local.workpaperbench.scripted-fixture'
RESERVED = '2026-10-22T20:29:41+00:00'
STARTED = '2026-10-22T20:29:42+00:00'


def observation(root, state='running', active='1', pid='29180', runs='1',
                exit_code='(never exited)', returncode=0, target=TARGET, extra=''):
    fields = [f'\tpath = {root / "supervisor.plist"}', f'\tstate = {state}',
              f'\tactive count = {active}', f'\truns = {runs}']
    if pid is not None:
        fields.append(f'\tpid = {pid}')
    if exit_code is not None:
        fields.append(f'\tlast exit code = {exit_code}')
    return subprocess.CompletedProcess([], returncode,
        target + ' = {\n' + '\n'.join(fields) + '\n' + extra + '}\n', '')


def terminal(root, started=STARTED, result_started=None):
    (root / 'launch-state.json').write_text(json.dumps({
        'started_at': started, 'one_attempt_only': True}))
    record = {'status': 'native_process_finished', 'started_at': result_started or started,
              'finished_at': '2026-10-22T20:33:49+00:00',
              'exit_code': 0, 'one_attempt_only': True}
    (root / 'launch-result.json').write_text(json.dumps(record))
    return record


class Polls:
    def __init__(self, records, publish=None):
        self.records = iter(records)
        self.publish = publish
        self.elapsed = 0
        self.queries = 0

    def query(self, target):
        assert target == TARGET
        self.queries += 1
        return next(self.records)

    def sleep(self, seconds):
        self.elapsed += seconds
        if self.publish:
            self.publish(self.queries)

    def wait(self, root):
        return wait_for_launcher(root, TARGET, RESERVED, query=self.query,
                                 sleep=self.sleep, clock=lambda: self.elapsed)


@pytest.mark.parametrize(('values', 'expected'), [
    ({'state': 'xpcproxy'}, 'startup'),
    ({}, 'running'),
    ({'state': 'xpcproxy', 'exit_code': '17'}, 'startup'),
    ({'exit_code': '17'}, 'running'),
    ({'state': 'not running', 'active': '0', 'pid': None, 'exit_code': '0'}, 'terminated'),
    ({'state': 'not running', 'active': '0', 'pid': None, 'exit_code': '23'}, 'terminated'),
    ({'state': 'not running', 'active': '0', 'pid': None}, 'unknown'),
    ({'state': 'not running', 'active': '0', 'exit_code': '23'}, 'unknown'),
    ({'state': 'not running', 'exit_code': '23'}, 'unknown'),
    ({'state': 'unknown'}, 'unknown'),
    ({'state': 'running', 'pid': None}, 'unknown'),
    ({'state': 'not running', 'active': '0', 'pid': None, 'runs': '0', 'exit_code': '23'}, 'unknown'),
    ({'runs': '2'}, 'unknown'),
    ({'returncode': 5}, 'unknown'),
    ({'target': TARGET + '-other'}, 'unknown'),
])
def test_consistent_current_job_fields(tmp_path, values, expected):
    assert launcher_status(observation(tmp_path, **values), TARGET,
                           tmp_path / 'supervisor.plist') == expected


def test_unknown_or_nested_fields_cannot_establish_status(tmp_path):
    other = observation(tmp_path / 'other')
    assert launcher_status(other, TARGET, tmp_path / 'supervisor.plist') == 'unknown'
    nested = observation(tmp_path, state='not running', active='0', pid=None,
                         extra='\tenvironment = {\n\t\tstate = running\n\t}\n')
    assert launcher_status(nested, TARGET, tmp_path / 'supervisor.plist') == 'unknown'
    repeated = observation(tmp_path, extra='\tstate = running\n')
    assert launcher_status(repeated, TARGET, tmp_path / 'supervisor.plist') == 'unknown'


def test_startup_running_then_current_terminal(tmp_path):
    polls = Polls([observation(tmp_path, state='xpcproxy'), observation(tmp_path)],
                  lambda count: terminal(tmp_path) if count == 2 else None)
    assert polls.wait(tmp_path)['exit_code'] == 0
    assert polls.queries == 2
    # Repeated polling of an already completed attempt never queries or submits.
    assert polls.wait(tmp_path)['exit_code'] == 0
    assert polls.queries == 2


def test_real_exit_without_terminal_requires_confirmation(tmp_path):
    exited = observation(tmp_path, state='not running', active='0', pid=None, exit_code='23')
    polls = Polls([observation(tmp_path), exited, exited])
    with pytest.raises(RuntimeError, match='^launcher_exited_without_final_record$'):
        polls.wait(tmp_path)
    assert polls.queries == 3
    assert not (tmp_path / 'launch-result.json').exists()


def test_delayed_and_temporarily_missing_status(tmp_path):
    missing = subprocess.CompletedProcess([], 5, '', 'not currently observable')
    polls = Polls([missing, observation(tmp_path, state='xpcproxy'), missing,
                   observation(tmp_path)],
                  lambda count: terminal(tmp_path) if count == 4 else None)
    assert polls.wait(tmp_path)['exit_code'] == 0
    assert polls.queries == 4


def test_one_exit_observation_then_missing_does_not_confirm_failure(tmp_path):
    exited = observation(tmp_path, state='not running', active='0', pid=None, exit_code='23')
    missing = subprocess.CompletedProcess([], 5, '', '')
    polls = Polls([exited, missing, observation(tmp_path)],
                  lambda count: terminal(tmp_path) if count == 3 else None)
    assert polls.wait(tmp_path)['exit_code'] == 0


@pytest.mark.parametrize('startup', [True, False])
def test_unresolved_status_has_bounded_wait(tmp_path, startup):
    status = observation(tmp_path, state='xpcproxy') if startup else subprocess.CompletedProcess([], 5, '', '')
    polls = Polls([status] * 5)
    with pytest.raises(RuntimeError, match='^launcher_status_unresolved$'):
        polls.wait(tmp_path)
    assert polls.elapsed == 60
    assert polls.queries == 5


def test_healthy_runtime_does_not_spend_the_later_status_grace(tmp_path):
    missing = subprocess.CompletedProcess([], 5, '', '')
    polls = Polls([observation(tmp_path)] * 6 + [missing] * 5)
    with pytest.raises(RuntimeError, match='^launcher_status_unresolved$'):
        polls.wait(tmp_path)
    assert polls.elapsed == 150
    assert polls.queries == 11


def test_status_query_timeout_is_unknown(monkeypatch, tmp_path):
    def timeout(*args, **kwargs):
        assert kwargs['timeout'] == 10
        raise subprocess.TimeoutExpired(args[0], 10)
    monkeypatch.setattr(subprocess, 'run', timeout)
    status = read_launchd(TARGET)
    assert launcher_status(status, TARGET, tmp_path / 'supervisor.plist') == 'unknown'


def test_current_terminal_precedes_unavailable_status_and_exit_race(tmp_path):
    record = terminal(tmp_path)
    def forbidden_query(target):
        pytest.fail('Current terminal record should take precedence')
    assert wait_for_launcher(tmp_path, TARGET, RESERVED, query=forbidden_query) == record
    (tmp_path / 'launch-result.json').unlink()
    def publish_during_exit_query(target):
        terminal(tmp_path)
        return observation(tmp_path, state='not running', active='0', pid=None, exit_code='0')
    assert wait_for_launcher(tmp_path, TARGET, RESERVED, query=publish_during_exit_query) == record


def test_stale_mismatched_and_partially_written_terminal_not_completion(tmp_path):
    terminal(tmp_path, started='2026-10-21T20:29:42+00:00')
    assert current_terminal_record(tmp_path, RESERVED) is None
    terminal(tmp_path, result_started='2026-10-22T20:29:43+00:00')
    assert current_terminal_record(tmp_path, RESERVED) is None
    (tmp_path / 'launch-result.json').write_text('{')
    assert current_terminal_record(tmp_path, RESERVED) is None
    polls = Polls([observation(tmp_path)], lambda count: terminal(tmp_path))
    assert polls.wait(tmp_path)['exit_code'] == 0
