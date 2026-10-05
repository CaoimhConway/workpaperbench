"""Counterexamples from the review. All submissions here are authored controls."""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from workpaperbench.grading import grade, replay

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import attempts
import collect_results
import native_run
import select_slots


def output(tmp_path, task='wp03'):
    trusted = ROOT / 'tasks' / task / 'tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    directory = tmp_path / 'submission'
    directory.mkdir(exist_ok=True)
    return trusted, answer, directory


def evaluate(directory, answer, trusted):
    (directory / 'answer.json').write_text(json.dumps(answer))
    return grade(directory, trusted)


@pytest.mark.parametrize('condition', ["date(published_on)<=date('2024-07-05')", "published_on<='2024-07-05' AND lower(period)='p2'"])
def test_valid_date_and_string_sql_are_accepted(tmp_path, condition):
    trusted, answer, directory = output(tmp_path)
    answer['answers'][1]['sql'] = "SELECT transfer_units AS value FROM releases WHERE period='P2' AND " + condition + ' ORDER BY published_on DESC LIMIT 1'
    assert evaluate(directory, answer, trusted)['complete']


@pytest.mark.parametrize('sql', ["SELECT julianday('now') AS value", "SELECT unixepoch() AS value", "SELECT julianday('2024-01-01','localtime') AS value", "SELECT unixepoch('subsec') AS value"])
def test_time_dependent_functions_remain_denied(sql):
    assert replay(sql, ROOT / 'tasks/wp03/tests/data.sqlite') is None


def test_extra_claim_does_not_erase_correct_requested_numbers(tmp_path):
    trusted, answer, directory = output(tmp_path, 'wp02')
    extra = copy.deepcopy(answer['answers'][0])
    extra['id'] = 'unrequested_total'
    answer['answers'].append(extra)
    verdict = evaluate(directory, answer, trusted)
    assert not verdict['complete']
    assert verdict['checks']['format'] is False
    assert verdict['checks']['numerical'] is True
    assert verdict['checks']['replay'] is None


def test_duplicate_requested_claim_is_not_resolved_by_grader(tmp_path):
    trusted, answer, directory = output(tmp_path, 'wp02')
    answer['answers'].append(copy.deepcopy(answer['answers'][0]))
    verdict = evaluate(directory, answer, trusted)
    assert not verdict['complete']
    assert verdict['checks']['numerical'] is None


def test_malformed_bytes_leave_unassessed_checks_unknown(tmp_path):
    trusted, _, directory = output(tmp_path)
    (directory / 'answer.json').write_text('{not json')
    flags = grade(directory, trusted)['checks']
    assert flags['format'] is False
    assert all(v is None for k, v in flags.items() if k != 'format')


def test_correct_conclusion_and_missing_citation_are_distinct(tmp_path):
    trusted, answer, directory = output(tmp_path, 'wp02')
    answer['conclusion']['evidence'] = ['ledger:events']
    verdict = evaluate(directory, answer, trusted)
    assert not verdict['complete']
    assert verdict['details']['conclusion']['verdict'] is True
    assert verdict['details']['conclusion']['evidence'] is False


def test_invalid_value_type_never_crashes_replay_diagnostics(tmp_path):
    trusted, answer, directory = output(tmp_path, 'wp02')
    answer['answers'][0]['value'] = '1200'
    verdict = evaluate(directory, answer, trusted)
    assert not verdict['complete']
    assert verdict['checks']['numerical'] is False


def install_history(monkeypatch, tmp_path, runs, jobs, manifest='new-freeze'):
    (tmp_path / 'config').mkdir()
    (tmp_path / 'config/freeze.json').write_text(json.dumps({'manifest_id':manifest}))
    slot = {'slot_id':'final-wp03-A-1','task':'wp03','arm':'A','repetition':1,'campaign':'final','split':'evaluation'}
    (tmp_path / 'config/schedule.json').write_text(json.dumps([slot]))
    monkeypatch.setattr(select_slots, 'ROOT', tmp_path)
    def fake_api(path):
        if '/jobs?' in path:
            return {'jobs':jobs}
        return {'workflow_runs':runs}
    monkeypatch.setattr(select_slots, 'api', fake_api)
    return slot


def test_same_run_previous_attempt_is_not_forgotten(monkeypatch, tmp_path):
    run = {'id':77,'display_title':'WPB::new-freeze::final'}
    job = {'id':5,'name':'trial-final-wp03-A-1','status':'completed','conclusion':'success','runner_id':1,'run_attempt':1}
    install_history(monkeypatch,tmp_path,[run],[job])
    monkeypatch.setenv('GITHUB_RUN_ID','77')
    monkeypatch.setenv('GITHUB_RUN_ATTEMPT','2')
    selected, attempted = select_slots.selection('final','new-freeze','all')
    assert selected == [] and 'final-wp03-A-1' in attempted


def test_new_experiment_is_not_suppressed_by_same_slot_name(monkeypatch, tmp_path):
    run = {'id':76,'display_title':'WPB::old-freeze::final'}
    job = {'id':5,'name':'trial-final-wp03-A-1','status':'completed','conclusion':'success','runner_id':1}
    install_history(monkeypatch,tmp_path,[run],[job])
    selected, attempted = select_slots.selection('final','new-freeze','all')
    assert len(selected) == 1 and not attempted


def test_legacy_manifest_is_read_from_execution_commit(monkeypatch):
    sha='a'*40
    payload=base64.b64encode(json.dumps({'manifest_id':'original-freeze'}).encode()).decode()
    monkeypatch.setattr(select_slots,'api',lambda path:{'content':payload})
    assert select_slots.run_manifest({'head_sha':sha,'display_title':'WorkpaperBench trials'},'final',{}) == 'original-freeze'


def test_paired_execution_preserves_declared_arm_order():
    schedule=json.loads((ROOT/'config/schedule.json').read_text())
    pairs=select_slots.pairs(schedule)
    assert len(pairs)==24
    assert [s for p in pairs for s in p['slots']]==[s['slot_id'] for s in schedule]
    for p in pairs:
        assert select_slots.job_slots({'name':'pair-freeze-'+p['pair_id']}) == p['slots']


def test_job_pagination_is_not_limited_to_first_hundred(monkeypatch):
    monkeypatch.setattr(select_slots,'api',lambda path:{'jobs':list(range(100)) if path.endswith('page=1') else [100]})
    assert len(list(select_slots.pages('synthetic/jobs?filter=all','jobs')))==101


def test_setup_receipt_becomes_explicit_infrastructure_failure(tmp_path,monkeypatch):
    monkeypatch.setattr(attempts,'ROOT',tmp_path)
    p=tmp_path/'reports/runs/test-freeze/final-wp03-A-1/record.json'
    attempts.write(p,{'status':'setup_started','verdict':None})
    attempts.finalize('test-freeze', ['final-wp03-A-1'])
    assert json.loads(p.read_text())['status']=='infra_failed'


def test_decoded_credentials_are_rejected_before_original_retention():
    key='synthetic-private-'+('abcd1234'*8)
    escaped=''.join('\\u'+format(ord(c),'04x') for c in key)
    assert native_run.credential_in(('{"value":"'+escaped+'"}').encode(),key)
    assert native_run.credential_in(('{bad:"'+escaped).encode(),key)


def test_retained_file_hash_is_separate_from_legacy_raw_hash(tmp_path):
    import io,zipfile
    (tmp_path/'config').mkdir()
    (tmp_path/'config/freeze.json').write_text('{"manifest_id":"test"}')
    slot={'slot_id':'final-wp03-A-1','campaign':'final','task':'wp03','arm':'A','repetition':1,'split':'evaluation'}
    (tmp_path/'config/schedule.json').write_text(json.dumps([slot]))
    record={**slot,'freeze_manifest_id':'test','answer_sha256':'legacy','run_id':'1','commit_sha':'a'*40,'github_run_attempt':'1'}
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as z:
        z.writestr('record.json',json.dumps(record))
        z.writestr('answer.json','{}\n')
    artifact={'id':123,'digest':'sha256:'+hashlib.sha256(buffer.getvalue()).hexdigest(),'declared_slots':[slot['slot_id']],'workflow_run':{'id':1,'head_sha':'a'*40,'run_attempt':1}}
    collect_results.import_archive(buffer.getvalue(),artifact,tmp_path)
    audit=json.loads((tmp_path/'reports/runs/test/final-wp03-A-1/artifact-audit.json').read_text())
    assert audit['retained_file_sha256']['answer.json']==hashlib.sha256(b'{}\n').hexdigest()
    assert audit['legacy_record_digest']=='legacy'
    assert not audit['original_bytes_available']


def test_reference_copies_use_current_reviewed_grader():
    for task in (ROOT/'tasks').glob('wp*'):
        for name in ('grading.py','sql_worker.py'):
            assert (task/'tests/workpaperbench'/name).read_bytes()==(ROOT/'workpaperbench'/name).read_bytes()


def test_authored_formula_control_exposes_accidentally_correct_number(tmp_path):
    # Separate control, not a repaired or rescored model submission.
    trusted, answer, directory = output(tmp_path)
    answer['answers'][2]['sql'] = "SELECT (SELECT transfer_units FROM releases WHERE release_id='r-p2-20240703') - (SELECT transfer_units FROM releases WHERE release_id='r-p1-20240701') * 100.0 / (SELECT transfer_units FROM releases WHERE release_id='r-p1-20240701') AS value"
    verdict = evaluate(directory, answer, trusted)
    assert verdict['checks']['numerical'] is True
    assert verdict['details']['claims']['as_of_growth']['original_replay'] is True
    assert verdict['details']['claims']['as_of_growth']['changed_replay'] is False
    assert not verdict['complete']
