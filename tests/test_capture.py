"""Synthetic protocol controls only. No public acquisition occurs in these tests."""
import importlib.util
import io
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('capture', Path(__file__).resolve().parent.parent / 'scripts/capture_logs.py')
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


@pytest.mark.parametrize('malformed', [False, True])
def test_fixed_six_request_capture_checks_address_abi(monkeypatch, malformed):
    sender = '0x' + '0' * 24 + '1' * 40
    if malformed:
        sender = '0x' + '1' * 64
    log = {'address':capture.ADDRESS, 'topics':[capture.TOPIC, sender, '0x'+'0'*24+'2'*40],
           'blockHash':'0x'+'3'*64, 'transactionHash':'0x'+'4'*64, 'logIndex':'0x0',
           'blockNumber':hex(capture.FIRST), 'data':'0x'+format(1_000_000,'064x'), 'removed':False}
    boundary = lambda number: {'number':hex(number), 'hash':'0x'+'3'*64, 'parentHash':'0x'+'5'*64, 'timestamp':hex(number)}
    replies = iter([[log], '0x1', boundary(capture.FIRST), boundary(capture.LAST), '0x6', '0x6000'])
    monkeypatch.setattr(capture, 'urlopen', lambda *args, **kwargs: io.BytesIO(json.dumps({'result':next(replies)}).encode()))
    monkeypatch.setattr(capture.time, 'sleep', lambda seconds: None)
    counts = {}
    if malformed:
        with pytest.raises(ValueError, match='address topic'):
            capture.acquire('https://synthetic.invalid', counts)
    else:
        result = capture.acquire('https://synthetic.invalid', counts)
        assert result['decimals'] == 6 and len(result['logs']) == 1
    assert counts == {'https://synthetic.invalid':6}
