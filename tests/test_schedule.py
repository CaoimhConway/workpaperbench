"""Control-plane resume states, including queued timestamps observed on Actions."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('schedule', Path(__file__).resolve().parent.parent / 'scripts/select_slots.py')
schedule = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schedule)


def test_queued_timestamp_does_not_count_as_a_started_trial():
    job = {'status':'queued', 'started_at':'2026-10-05T05:15:21Z', 'runner_id':None, 'steps':[]}
    assert not schedule.job_started(job)
    assert not schedule.job_started({**job, 'status':'completed', 'conclusion':'cancelled'})


def test_allocated_failed_or_cancelled_job_stays_attempted():
    job = {'status':'completed', 'conclusion':'cancelled', 'runner_id':123, 'steps':[]}
    assert schedule.job_started(job)
    assert schedule.job_started({'status':'completed', 'conclusion':'failure', 'steps':[{'started_at':'2026-10-05T05:15:24Z'}]})
