import copy
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import sqlite3
import sys
import types

import pytest

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_workflow_grading_contract_revision import ALTERNATIVES, DEFINITIONS
from validate_workflow_quality import artifacts

MODULE = importlib.util.spec_from_file_location('workpaperbench.grading_contract', ROOT / 'config/scorers/workflow-1.2.1.py')
SCORER = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(SCORER)


def read(path):
    return json.loads(path.read_text())


def test_revision_preserves_original_observations_targets_scorer_and_controls():
    prior, current = load(ROOT, 'workflow-v11'), load(ROOT, 'workflow-v12')
    assert current['prior_catalog'] == prior['manifest_id']
    for field in ('scorer_version', 'scorer_sha256', 'sql_worker_sha256'):
        assert current[field] == prior[field]
    for key in current['tasks']:
        _, before, old = load(ROOT, 'workflow-v11', key)
        _, after, new = load(ROOT, 'workflow-v12', key)
        assert (before['split'], before['source_group']) == (after['split'], after['source_group'])
        expected = copy.deepcopy(read(old / 'tests/gold.json'))
        actual = read(new / 'tests/gold.json')
        expected.update(task_id=after['task_id'], hashes=actual['hashes'])
        for name, options in ALTERNATIVES.get(key, {}).items():
            expected['claims'][name]['evidence'].extend(options)
        if key == 'b01':
            expected['controls'].append(actual['controls'][-1])
            for name in ('reserve_coverage', 'reserve_bridge'):
                expected['tables'][name]['context_evidence_allowed'].extend(['b01:s03', 'b01:s06'])
        assert actual == expected
        for path in old.rglob('*'):
            if not path.is_file():
                continue
            relative = path.relative_to(old)
            if str(relative) == 'tests/gold.json' or (path.name == 'authoring.json' and key in ALTERNATIVES.keys() | DEFINITIONS.keys()):
                continue
            if path.name == 'output_contract.json' and key in DEFINITIONS:
                contract = read(path)
                contract['definitions'].update(DEFINITIONS[key])
                assert contract == read(new / relative)
            elif key == 'b01' and path.name == 'instruction.md':
                assert 'Reserve change is (June cash + June government debt) minus (May cash + May government debt).' in (new / relative).read_text()
            else:
                assert path.read_bytes().replace(before['task_id'].encode(), after['task_id'].encode()) == (new / relative).read_bytes()
        assert {p.relative_to(new) for p in new.rglob('*') if p.is_file()} - {
            p.relative_to(old) for p in old.rglob('*') if p.is_file()} == ({Path('tests/control-reported-reserve.sqlite')} if key == 'b01' else set())


@pytest.mark.parametrize('key', ALTERNATIVES)
def test_narrow_sufficient_evidence_preserves_original_alternatives(key):
    old = read(ROOT / 'datasets/workflow-v11/tasks' / key / 'tests/gold.json')
    new = read(ROOT / 'datasets/workflow-v12/tasks' / key / 'tests/gold.json')
    for name, options in ALTERNATIVES[key].items():
        spec = new['claims'][name]
        for option in old['claims'][name]['evidence'] + options:
            assert SCORER.supported(option, spec['evidence'], spec['context_evidence_allowed'])
        for option in options:
            assert not SCORER.supported(option, old['claims'][name]['evidence'], old['claims'][name]['context_evidence_allowed'])
            assert not SCORER.supported(option + ['unknown:s99'], spec['evidence'], spec['context_evidence_allowed'])
        assert not SCORER.supported([], spec['evidence'], spec['context_evidence_allowed'])


def test_a02_period_definition_units_and_wrong_source_rejection():
    task = ROOT / 'datasets/workflow-v12/tasks/a02'
    source = next(x for x in read(task / 'environment/evidence.json') if x['id'] == 'a02:s03')
    assert all(text in source['text'] for text in ('finance-lease', 'USD 43,585 million in 2025', 'USD 52,103 million in 2024'))
    assert 43585 < 52103
    spec = read(task / 'tests/gold.json')['claims']['claim_1']
    assert spec['verdict'] == 'contradicted'
    for evidence in (['a02:s01'], ['a02:s02'], ['a02:s03', 'a02:s02']):
        assert not SCORER.supported(evidence, spec['evidence'], spec['context_evidence_allowed'])


def test_b01_observation_dates_are_context_not_sufficient_numeric_evidence():
    gold = read(ROOT / 'datasets/workflow-v12/tasks/b01/tests/gold.json')
    for name in ('reserve_coverage', 'reserve_bridge'):
        spec = gold['tables'][name]
        assert SCORER.supported(['b01:s01', 'b01:s03', 'b01:s04', 'b01:s06'], spec['evidence'], spec['context_evidence_allowed'])
        for insufficient in (['b01:s03', 'b01:s06'], ['b01:s01'], ['b01:s04'], ['b01:s01', 'b01:s04', 'unknown:s99']):
            assert not SCORER.supported(insufficient, spec['evidence'], spec['context_evidence_allowed'])


def rows(task, database, name):
    with sqlite3.connect(task / 'tests' / database) as db:
        result = db.execute((task / 'solution' / (name + '.sql')).read_text())
        return [dict(zip([c[0] for c in result.description], row)) for row in result]


def test_b01_independent_component_and_reported_changes():
    task = ROOT / 'datasets/workflow-v12/tasks/b01'
    gold = read(task / 'tests/gold.json')
    controls = {x['name']: x['database'] for x in gold['controls']}
    base = rows(task, 'data.sqlite', 'reserve_bridge')[0]
    assert base['reserve_change_usd'] == (3475633 + 5880883) - (2210784 + 4883011)
    for name, bridge_delta, residual in [('independent_disclosure_discrepancy', -17, 17),
            ('reported_reserve_changes_with_components_fixed', 0, -19)]:
        db = controls[name]
        bridge = rows(task, db, 'reserve_bridge')[0]
        assert bridge['reserve_change_usd'] == base['reserve_change_usd'] + bridge_delta
        coverage = rows(task, db, 'reserve_coverage')
        assert next(r for r in coverage if r['report_date'] == '2025-05-31')['residual_usd'] == residual
        assert next(r for r in coverage if r['report_date'] == '2025-06-30')['residual_usd'] == 0
        with sqlite3.connect(task / 'tests' / db) as conn:
            data = conn.execute('SELECT report_date,cash_equivalents_usd+us_government_debt_usd,reported_reserve_fv_usd FROM reserve_reports ORDER BY report_date').fetchall()
        assert data[0][1] - data[0][2] == residual
        assert bridge['reserve_change_usd'] == data[1][1] - data[0][1]


def test_clarified_table_bases_preserve_independent_reported_amounts():
    def control(key, name):
        task = ROOT / 'datasets/workflow-v12/tasks' / key
        gold = read(task / 'tests/gold.json')
        db = next(x['database'] for x in gold['controls'] if x['name'] == 'independent_disclosure_discrepancy')
        return rows(task, db, name)
    parent = next(r for r in control('b10', 'parent_earnings_bridge') if r['year'] == 2025)
    cash = next(r for r in control('b10', 'consolidated_cash_bridge') if r['year'] == 2025)
    assert parent['parent_income_usd_million'] == 67002
    assert cash['parent_income_usd_million'] == 66968
    assert parent['residual_usd_million'] == 67002 - 66968 == 34
    assert parent['operating_earnings_usd_million'] == 67002 - 30737 - (-8255)
    adobe = next(r for r in control('c02', 'operating_reconciliation') if r['period'] == 'Q4FY2025')
    assert adobe['adjusted_operating_income_usd_million'] == 2824
    assert adobe['residual_usd_million'] == 2278 + 563 - 2824 == 17
    visa = next(r for r in control('c03', 'net_income_reconciliation') if r['period'] == 'Q4FY2025')
    growth = next(r for r in control('c03', 'income_growth_bridge') if r['window'] == 'Q4FY')
    assert visa['adjusted_income_usd_million'] == 5124 + 713 == 5837
    assert visa['residual_usd_million'] == 5837 - 5803 == 34
    assert growth['adjusted_change_usd_million'] == 5803 - 5425 == 378
    assert growth['gap_change_usd_million'] == (5803 - 5124) - (5425 - 5318) == 572


@pytest.mark.skipif(platform.system() != 'Linux', reason='Full SQL worker resource limits require Linux')
@pytest.mark.parametrize('key,case', [('a02', 'sufficient'), ('a02', 'insufficient'), ('a02', 'wrong_source'),
    ('b01', 'date_context'), ('b01', 'dates_only'), ('b01', 'reported_bridge'), ('b01', 'frozen_bridge'), ('b01', 'frozen_residual')])
def test_complete_submission_to_verdict(tmp_path, key, case):
    _, _, task = load(ROOT, 'workflow-v12', key)
    files = artifacts(task, 'reference', [])
    if case == 'frozen_residual':
        files = artifacts(task, 'constant_residual', [('reserve_coverage', 'residual_usd')])
    answer = json.loads(files['answer.json'])
    if key == 'a02':
        answer['claims'][0]['evidence'] = {'sufficient': ['a02:s03'], 'insufficient': ['a02:s01'], 'wrong_source': ['a02:s02']}[case]
    else:
        entry = next(x for x in answer['tables'] if x['id'] == 'reserve_bridge')
        entry['evidence'] = ['b01:s01', 'b01:s03', 'b01:s04', 'b01:s06']
        if case == 'dates_only':
            entry['evidence'] = ['b01:s03', 'b01:s06']
        if case == 'reported_bridge':
            text = files['reserve_bridge.sql'].decode().replace('(c.cash_equivalents_usd+c.us_government_debt_usd)-(p.cash_equivalents_usd+p.us_government_debt_usd) reserve_change_usd', 'c.reported_reserve_fv_usd-p.reported_reserve_fv_usd reserve_change_usd')
            files['reserve_bridge.sql'] = text.encode()
        if case == 'frozen_bridge':
            spec = read(task / 'tests/gold.json')['tables']['reserve_bridge']
            files['reserve_bridge.sql'] = ('SELECT ' + ','.join(repr(v) + ' AS "' + c + '"' for c, v in zip(spec['columns'], spec['rows'][0]))).encode()
    files['answer.json'] = json.dumps(answer).encode()
    trusted = tmp_path / 'trusted'
    shutil.copytree(task / 'tests', trusted)
    path = trusted / 'workpaperbench/workflow_grading.py'
    module = types.ModuleType('workpaperbench.contract_revision_test')
    module.__file__, module.__package__ = str(path), 'workpaperbench'
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    directory = tmp_path / 'artifacts'
    directory.mkdir()
    for name, raw in files.items():
        (directory / name).write_bytes(raw)
    verdict = module.grade(directory, trusted)
    expected = case in ('sufficient', 'date_context')
    assert verdict['complete'] is expected
    assert verdict['checks']['numerical_tables']
    if case in ('reported_bridge', 'frozen_bridge', 'frozen_residual'):
        assert verdict['checks']['evidence']
        assert not verdict['checks']['robustness']
        if case == 'frozen_residual':
            controls = verdict['details']['tables']['reserve_coverage']['controls']
            assert {name for name, passed in controls.items() if not passed} == {
                'independent_disclosure_discrepancy', 'reported_reserve_changes_with_components_fixed'}
    elif not expected:
        assert not verdict['checks']['evidence']
        assert verdict['checks']['robustness']
