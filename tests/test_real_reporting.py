"""Reporting does not pool the new source-backed experiment with historical results."""
import copy
import json
from pathlib import Path

from workpaperbench.real_report import fraction, interpretation, report_real

ROOT = Path(__file__).resolve().parents[1]


def test_pending_counts_remain_unassessed():
    assert fraction(0, 0) == 'Pending'
    summary = {'evaluation': {arm: {'verified': 0, 'scheduled': 15, 'assessed': 0} for arm in ('A', 'B')}}
    assert 'pending' in interpretation(summary, 'pending')
    assert 'incomplete verdict coverage' in interpretation(summary, 'measured')


def test_current_manifest_has_separate_48_slot_report(tmp_path):
    manifest = json.loads((ROOT / 'datasets/real-v1/manifest.json').read_text())
    (tmp_path / 'datasets/real-v1').mkdir(parents=True)
    (tmp_path / 'datasets/real-v1/manifest.json').write_text(json.dumps(manifest))
    schedule = json.loads((ROOT / manifest['schedule']).read_text())
    (tmp_path / manifest['schedule']).write_text(json.dumps(schedule))
    (tmp_path / 'README.md').write_text('No combined markers')
    result = report_real(tmp_path)
    assert len(result['slots']) == 48
    assert result['retained_answers'] == 0
    assert result['status'] == 'pending'
    assert result['summary']['evaluation']['A']['scheduled'] == 15
    assert result['summary']['development']['B']['scheduled'] == 9
    assert 'Historical results are a separate study' in (tmp_path / 'reports/real-v1/results.md').read_text()
