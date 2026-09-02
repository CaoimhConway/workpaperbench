"""Synthetic report controls and checks of retained campaign receipts."""
import json
from decimal import Decimal
from pathlib import Path
from workpaperbench.cli import report, summarize


def test_retained_campaign_cost_totals_match_decimal_receipts():
    root = Path(__file__).resolve().parents[1]
    rows = [json.loads(path.read_text()) for path in
            sorted((root / 'reports/runs').glob('final-*/record.json'))]
    assert len(rows) == 48
    summary = summarize(rows)
    for split in ('evaluation', 'development'):
        for arm in ('A', 'B'):
            receipts = [Decimal(str(row['provider_cost_delta_usd'])) for row in rows
                        if row['split'] == split and row['arm'] == arm]
            assert summary[split][arm]['known_slot_cost_usd'] == float(sum(receipts, Decimal(0)))


def test_partial_denominators_and_failure_causes(tmp_path):
    (tmp_path / 'config').mkdir()
    (tmp_path / 'reports/runs/synthetic').mkdir(parents=True)
    (tmp_path / 'config/freeze.json').write_text(json.dumps({'manifest_id':'synthetic-report-control'}))
    slots=[{'slot_id':'synthetic-1','campaign':'final','task':'wp03','arm':'A','repetition':1,'split':'evaluation'},
           {'slot_id':'synthetic-2','campaign':'final','task':'wp03','arm':'A','repetition':2,'split':'evaluation'}]
    (tmp_path / 'config/schedule.json').write_text(json.dumps(slots))
    record={**slots[0],'status':'task_failed','verdict':{'complete':False,'checks':{'numerical':True,'evidence_context':False,'availability':True,'conclusion':True,'replay':False,'format':True},'errors':['synthetic-control']}}
    (tmp_path / 'reports/runs/synthetic/record.json').write_text(json.dumps(record))
    result=report(tmp_path)
    summary=result['summary']['evaluation']['A']
    assert summary['scheduled']==2
    assert summary['verified']==0
    assert summary['numerical_correct_full_failed']==1
    assert summary['gap_causes_nonexclusive']=={'evidence_requirements':1,'replay':1}
    assert result['slots'][1]['status']=='unrecorded'
    assert result['slots'][1]['verdict'] is None
    assert '| wp03 | A | 0 / 2 | Not assessed | 0 / 2 |' in (tmp_path / 'reports/results.md').read_text()


def test_unscheduled_or_mismatched_final_record_fails(tmp_path):
    import pytest
    (tmp_path / 'config').mkdir()
    directory = tmp_path / 'reports/runs/wrong'
    directory.mkdir(parents=True)
    (tmp_path / 'config/freeze.json').write_text(json.dumps({'manifest_id':'synthetic-report-control'}))
    slot = {'slot_id':'synthetic-1','campaign':'final','task':'wp03','arm':'A','repetition':1,'split':'evaluation'}
    (tmp_path / 'config/schedule.json').write_text(json.dumps([slot]))
    record = {**slot,'arm':'B','status':'infra_failed','verdict':None}
    (directory / 'record.json').write_text(json.dumps(record))
    with pytest.raises(ValueError,match='identity mismatch'):
        report(tmp_path)
    record['slot_id'] = 'unscheduled'
    (directory / 'record.json').write_text(json.dumps(record))
    with pytest.raises(ValueError,match='unscheduled'):
        report(tmp_path)
