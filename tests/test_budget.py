"""Synthetic metadata controls. No network or inference calls."""
import importlib.util
import json
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('native_runner', Path(__file__).resolve().parent.parent / 'scripts/native_run.py')
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_lifetime_cap_and_reservation():
    snapshot={'lifetime_limit_usd':20,'remaining_usd':20,'funded_remaining_usd':20,'byok_usage_usd':0,'reset_is_null':True}
    assert runner.preflight(snapshot,0.2,48) is None
    for field,value in [('lifetime_limit_usd',0),('lifetime_limit_usd',21),('remaining_usd',9),('reset_is_null',False),('byok_usage_usd',1)]:
        changed={**snapshot,field:value}
        assert runner.preflight(changed,0.2,48) is not None


def test_pilot_drives_conservative_reserve_and_finished_slots_stay_finished():
    slots=[{'slot_id':'synthetic-1'},{'slot_id':'synthetic-2'}]
    records=[{'campaign':'pilot','provider_cost_delta_usd':0.03},
             {'slot_id':'synthetic-1','campaign':'final','status':'task_failed'}]
    reserve,remaining=runner.final_reservation(slots,records)
    assert reserve==0.3
    assert remaining==1


def test_live_driver_cannot_run_on_local_device(monkeypatch):
    monkeypatch.delenv('GITHUB_ACTIONS',raising=False)
    with pytest.raises(ValueError,match='require_dedicated'):
        runner.execute('pilot','pilot-wp01-A-1')


def test_decoded_artifact_scan_catches_json_escaped_credential():
    key = 'synthetic-private-value-' + '0123456789' * 4
    escaped = ''.join('\\u' + format(ord(character), '04x') for character in key)
    wire = ('{"sql":"' + escaped + '"}').encode()
    assert runner.credential_in(wire, key)
    canonical = json.dumps(json.loads(wire)).encode()
    assert runner.credential_in(canonical, key)


def test_failure_diagnostics_emit_codes_without_untrusted_text(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    raw = tmp_path / '.raw'
    raw.mkdir()
    path = raw / 'failure.txt'
    path.write_text('Invalid model ID\nUntrusted candidate prose and private-value-1234567890')
    codes = runner.failure_codes(path)
    assert codes == ['invalid_model_id']
    assert 'private-value' not in json.dumps(codes)
    assert runner.failure_codes(tmp_path / 'missing') == []
