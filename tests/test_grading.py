import copy
import json
from pathlib import Path
import shutil

import pytest

from workpaperbench.grading import grade, parse, replay

ROOT = Path(__file__).resolve().parent.parent
TASKS = sorted(p.name for p in (ROOT / 'sources').glob('wp*.json'))


def submission(tmp_path, reference):
    target = tmp_path / 'output'
    target.mkdir(exist_ok=True)
    (target / 'answer.json').write_text(json.dumps(reference))
    return target


@pytest.mark.parametrize('task', TASKS)
def test_reference(tmp_path, task):
    trusted = ROOT / 'tasks' / Path(task).stem / 'tests'
    reference = json.loads((trusted / 'reference.json').read_text())
    assert grade(submission(tmp_path, reference), trusted)['complete']


@pytest.mark.parametrize('task', TASKS)
def test_alternative_cte_and_subquery(tmp_path, task):
    trusted = ROOT / 'tasks' / Path(task).stem / 'tests'
    reference = json.loads((trusted / 'reference.json').read_text())
    for form in ('WITH calculated AS ({sql}) SELECT value FROM calculated',
                 'SELECT value FROM ({sql})'):
        alternate = copy.deepcopy(reference)
        for claim in alternate['answers']:
            if claim['sql']:
                claim['sql'] = form.format(sql=claim['sql'])
        assert grade(submission(tmp_path, alternate), trusted)['complete']


@pytest.mark.parametrize('task', TASKS)
@pytest.mark.parametrize('control', ['constant', 'table_constant', 'all_citations', 'always_abstain', 'wrong_unit', 'wrong_scalar', 'wrong_evidence', 'always_skeptical'])
def test_wrong_submissions(tmp_path, task, control):
    trusted = ROOT / 'tasks' / Path(task).stem / 'tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    table = next(iter(json.loads((ROOT / 'sources' / task).read_text())['tables']))
    answered = next(a for a in answer['answers'] if a['status'] == 'answered')
    if control == 'constant':
        answered['sql'] = f"SELECT {answered['value']} AS value"
    elif control == 'table_constant':
        answered['sql'] = f"SELECT {answered['value']} AS value FROM {table} LIMIT 1"
    elif control == 'all_citations':
        answered['evidence'] = [record['id'] for record in json.loads((trusted / 'evidence.json').read_text())]
    elif control == 'always_abstain':
        answered.update(status='insufficient_evidence', value=None, sql=None, reason_code='missing_required_input')
    elif control == 'wrong_unit':
        answered['unit'] = 'usd'
    elif control == 'wrong_scalar':
        answered['value'] += 1
    elif control == 'wrong_evidence':
        answered['evidence'] = ['irrelevant:source']
    elif answer['conclusion']:
        answer['conclusion']['verdict'] = 'not_established' if answer['conclusion']['verdict'] != 'not_established' else 'supported'
    else:
        answer['conclusion'] = {'verdict':'not_established','reason_code':'missing_required_evidence','evidence':answered['evidence']}
    assert not grade(submission(tmp_path, answer), trusted)['complete']


@pytest.mark.parametrize('sql', ["DROP TABLE expenses", "ATTACH DATABASE '/tmp/escape.sqlite' AS x", "SELECT load_extension('/tmp/x') AS value", 'PRAGMA database_list', 'SELECT randomblob(100000000) AS value', 'SELECT 1 AS value UNION ALL SELECT 2', 'SELECT 1 AS value,2 AS other', 'SELECT 1 AS value', 'SELECT 1 AS value\nSELECT 2', 'WITH RECURSIVE t(n) AS (VALUES(1) UNION ALL SELECT n+1 FROM t) SELECT SUM(n) AS value FROM t'])
def test_sql_boundary(sql):
    value = replay(sql, ROOT / 'tasks/wp01/tests/data.sqlite')
    if sql == 'SELECT 1 AS value':
        assert value == 1
    else:
        assert value is None


@pytest.mark.parametrize('mode', ['symlink', 'extra', 'directory', 'oversize', 'fifo'])
def test_artifact_boundary(tmp_path, mode):
    trusted = ROOT / 'tasks/wp01/tests'
    target = tmp_path / 'output'
    target.mkdir()
    answer = target / 'answer.json'
    if mode == 'symlink':
        answer.symlink_to(trusted / 'reference.json')
    elif mode == 'extra':
        shutil.copy(trusted / 'reference.json', answer)
        (target / 'data.sqlite').write_bytes(b'injected')
    elif mode == 'directory':
        answer.mkdir()
    elif mode == 'oversize':
        answer.write_bytes(b' ' * 65537)
    else:
        import os
        os.mkfifo(answer)
    assert not grade(target, trusted)['complete']


def test_duplicate_json_and_nonfinite():
    with pytest.raises(ValueError):
        parse('{"value":1,"value":2}')
    with pytest.raises(ValueError):
        parse('{"value":NaN}')


def test_pristine_input_tamper(tmp_path):
    trusted = tmp_path / 'trusted'
    shutil.copytree(ROOT / 'tasks/wp01/tests', trusted)
    reference = json.loads((trusted / 'reference.json').read_text())
    (trusted / 'data.sqlite').write_bytes(b'tampered')
    assert grade(submission(tmp_path, reference), trusted)['errors'] == ['trusted_input_changed']


def test_wrong_period_correct_scalars(tmp_path):
    trusted = ROOT / 'tasks/wp01/tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    for claim in answer['answers']:
        claim['evidence'] = ['filing:comparative']
    result = grade(submission(tmp_path, answer), trusted)
    assert result['checks']['numerical'] is True
    assert result['checks']['evidence_context'] is False
    assert not result['complete']


def test_filing_document_evidence_alternative(tmp_path):
    trusted = ROOT / 'tasks/wp01/tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    for claim in answer['answers']:
        claim['evidence'] = ['filing:table']
    assert grade(submission(tmp_path, answer), trusted)['complete']
    for claim in answer['answers']:
        claim['evidence'] = ['filing:q2', 'filing:h1']
    assert grade(submission(tmp_path, answer), trusted)['complete']


def test_event_identity_alternative_and_transaction_dedup_wrong(tmp_path):
    trusted = ROOT / 'tasks/wp02/tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    claim = answer['answers'][0]
    claim['sql'] = "SELECT SUM(amount_units) AS value FROM (SELECT DISTINCT event_id,tx_id,event_kind,amount_units FROM events WHERE event_kind='transfer')"
    assert grade(submission(tmp_path, answer), trusted)['complete']
    claim['sql'] = "SELECT SUM(amount_units) AS value FROM (SELECT tx_id,MAX(amount_units) amount_units FROM events WHERE event_kind='transfer' GROUP BY tx_id)"
    assert not grade(submission(tmp_path, answer), trusted)['complete']


def test_definition_mismatch(tmp_path):
    trusted = ROOT / 'tasks/wp05/tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    answer['answers'][1]['value'] = 65
    answer['answers'][1]['sql'] = answer['answers'][0]['sql']
    assert not grade(submission(tmp_path, answer), trusted)['complete']
