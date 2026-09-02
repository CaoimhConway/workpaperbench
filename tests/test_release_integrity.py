"""Small release controls. These fixtures are not recorded model trials."""
import json
from pathlib import Path

import pytest

from workpaperbench.cli import update_readme
from workpaperbench.grading import close, grade, replay

ROOT = Path(__file__).resolve().parent.parent


def test_out_of_float_range_integer_is_a_failure_not_a_grader_crash(tmp_path):
    trusted = ROOT / 'tasks/wp02/tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    answer['answers'][0]['value'] = 10**1000
    (tmp_path / 'answer.json').write_text(json.dumps(answer))
    verdict = grade(tmp_path, trusted)
    assert verdict['complete'] is False
    assert verdict['checks']['numerical'] is False
    assert close(10**1000, 1200, 1e-6) is False


def test_latest_release_can_use_a_window_function(tmp_path):
    trusted = ROOT / 'tasks/wp03/tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    answer['answers'][1]['sql'] = (
        "WITH ranked AS (SELECT period, transfer_units, "
        "ROW_NUMBER() OVER (PARTITION BY period ORDER BY published_on DESC) AS n "
        "FROM releases WHERE date(published_on)<=date('2024-07-05')) "
        "SELECT transfer_units AS value FROM ranked WHERE lower(period)='p2' AND n=1"
    )
    (tmp_path / 'answer.json').write_text(json.dumps(answer))
    assert grade(tmp_path, trusted)['complete'] is True


def test_blob_cannot_reintroduce_wall_clock_dates():
    assert replay("SELECT julianday(CAST('now' AS BLOB)) AS value", ROOT / 'tasks/wp03/tests/data.sqlite') is None


def test_worker_does_not_load_site_customizations(monkeypatch):
    import workpaperbench.grading as grading
    real_run = grading.subprocess.run
    commands = []
    def traced(command, **kwargs):
        commands.append(command)
        return real_run(command, **kwargs)
    monkeypatch.setattr(grading.subprocess, 'run', traced)
    assert replay('SELECT 1 AS value', ROOT / 'tasks/wp03/tests/data.sqlite') == 1
    assert commands[0][1:3] == ['-I', '-S']


def partial_summary():
    arm = {'verified': 0, 'scheduled': 1, 'assessed': 0}
    return {'evaluation': {'A': dict(arm), 'B': dict(arm)}}


def test_readme_refresh_is_bounded_and_does_not_claim_unrun_accuracy(tmp_path):
    path = tmp_path / 'README.md'
    prefix, suffix = '# WorkpaperBench\n\n', '\n\n## Limits\nUnchanged.\n'
    path.write_text(prefix + '<!-- study-results:start -->old<!-- study-results:end -->' + suffix)
    result = {
        'slots': [{'status': 'unrecorded', 'verdict': None}, {'status': 'running', 'verdict': None}],
        'reviews': {}, 'summary': partial_summary(), 'reviewed_summary': partial_summary(),
    }
    update_readme(tmp_path, result)
    text = path.read_text()
    assert text.startswith(prefix) and text.endswith(suffix)
    assert '**Partial campaign.**' in text
    assert 'Not assessed' in text
    assert 'treatment-effect claim' in text
    assert '0%' not in text
    update_readme(tmp_path, result)
    assert path.read_text() == text


def test_readme_marker_mistake_fails_loudly(tmp_path):
    path = tmp_path / 'README.md'
    path.write_text('<!-- study-results:start -->unclosed')
    with pytest.raises(ValueError, match='markers'):
        update_readme(tmp_path, {})


def test_remaining_reserve_uses_current_history_not_a_cold_checkout(tmp_path, monkeypatch):
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    import attempts
    import select_slots
    available = [{'slot_id': f'final-wp03-A-{i}', 'campaign': 'final'} for i in (1, 2, 3)]
    monkeypatch.setattr(attempts, 'ROOT', tmp_path)
    monkeypatch.setattr(select_slots, 'selection', lambda *args: (available, {}))
    monkeypatch.setenv('GITHUB_RUN_ATTEMPT', '1')
    monkeypatch.setenv('GITHUB_RUN_ID', '1')
    monkeypatch.setenv('GITHUB_SHA', 'a' * 40)
    attempts.receipt('final', 'test-freeze', [a['slot_id'] for a in available[:2]])
    first = json.loads((tmp_path / 'reports/runs/test-freeze/final-wp03-A-1/record.json').read_text())
    second = json.loads((tmp_path / 'reports/runs/test-freeze/final-wp03-A-2/record.json').read_text())
    assert first['remaining_planned_slots'] == 3
    assert second['remaining_planned_slots'] == 2


def test_structurally_rejected_output_never_runs_sql(tmp_path, monkeypatch):
    import workpaperbench.grading as grading
    trusted = ROOT / 'tasks/wp02/tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    answer['answers'].append({**answer['answers'][0], 'id': 'extra'})
    (tmp_path / 'answer.json').write_text(json.dumps(answer))
    def forbidden(*args):
        raise AssertionError('structurally rejected SQL must not execute')
    monkeypatch.setattr(grading, 'replay', forbidden)
    verdict = grade(tmp_path, trusted)
    assert verdict['checks']['format'] is False
    assert verdict['checks']['numerical'] is True
    assert all(v is None for k, v in verdict['checks'].items() if k not in ('format', 'numerical'))


def test_invalid_evidence_syntax_does_not_imply_incorrect_arithmetic(tmp_path, monkeypatch):
    import workpaperbench.grading as grading
    trusted = ROOT / 'tasks/wp02/tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    answer['answers'][0]['evidence'] = ['prose citation without an identifier']
    (tmp_path / 'answer.json').write_text(json.dumps(answer))
    verdict = grade(tmp_path, trusted)
    assert verdict['checks']['format'] is True
    assert verdict['checks']['numerical'] is True
    assert verdict['checks']['evidence_context'] is False
    assert verdict['checks']['replay'] is True


def test_receipts_are_scoped_to_experiment_and_rechecked_before_inference(tmp_path, monkeypatch):
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    import attempts
    import select_slots
    identifier = 'final-wp03-A-1'
    monkeypatch.setattr(attempts, 'ROOT', tmp_path)
    monkeypatch.setattr(select_slots, 'selection', lambda *args: ([{'slot_id': identifier}], {}))
    monkeypatch.setattr(select_slots, 'history', lambda *args: {})
    monkeypatch.setenv('GITHUB_RUN_ATTEMPT', '1')
    monkeypatch.setenv('GITHUB_RUN_ID', '5')
    monkeypatch.setenv('GITHUB_SHA', 'a' * 40)
    attempts.receipt('final', 'old', [identifier])
    attempts.receipt('final', 'new', [identifier])
    attempts.check('final', 'new', [identifier])
    monkeypatch.setattr(select_slots, 'history', lambda *args: {identifier: {'run_id': 4}})
    with pytest.raises(ValueError, match='previously_attempted'):
        attempts.check('final', 'new', [identifier])
    monkeypatch.setenv('GITHUB_RUN_ATTEMPT', '2')
    with pytest.raises(ValueError, match='same_run'):
        attempts.receipt('final', 'newer', [identifier])


def test_documented_demo_reads_preserved_workpaper():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, '-m', 'workpaperbench.cli', 'demo'],
                            cwd=ROOT, capture_output=True, text=True, check=True)
    assert 'P1=100, P2=120, reported growth=20%' in result.stdout
    assert 'Original complete=False' in result.stdout
    assert 'correct growth=25%' in result.stdout


def test_public_reading_path_links_resolve():
    import re
    from urllib.parse import unquote
    for name in ('README.md', 'docs/METHODOLOGY.md', 'docs/TASK_AUTHORING.md', 'reports/case-study.md'):
        path = ROOT / name
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', path.read_text()):
            if '://' in target or target.startswith('#'):
                continue
            assert (path.parent / unquote(target.split('#')[0])).exists(), (name, target)
