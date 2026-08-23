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


def test_fixed_48_slot_schedule_and_origin_manifest():
    import json
    from collections import Counter
    root = Path(__file__).resolve().parent.parent
    slots = json.loads((root / 'config/schedule.json').read_text())
    assert len(slots) == len({s['slot_id'] for s in slots}) == 48
    assert Counter(s['split'] for s in slots) == {'evaluation':30,'development':18}
    assert set(Counter((s['task'],s['arm']) for s in slots).values()) == {3}
    for pair_index in range(24):
        pair = slots[pair_index*2:pair_index*2+2]
        task_index = int(pair[0]['task'][2:])-1
        repetition = pair[0]['repetition']
        expected = ['A','B'] if (task_index+repetition-1)%2 == 0 else ['B','A']
        assert [s['arm'] for s in pair] == expected
        source = json.loads((root / 'sources' / (pair[0]['task']+'.json')).read_text())
        assert source['origin'] in {'primary_filing_facts','synthetic','synthetic_acquisition_downgrade'}
        assert all(s['split'] == source['split'] for s in pair)
