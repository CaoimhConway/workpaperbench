import importlib.util
import json
from pathlib import Path
import sqlite3
import sys

import pytest

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_workflow_contract_adjudication import construct

module = importlib.util.spec_from_file_location('workpaperbench.adjudication_scorer', ROOT / 'config/scorers/workflow-1.2.1.py')
SCORER = importlib.util.module_from_spec(module)
module.loader.exec_module(SCORER)
read = lambda p: json.loads(p.read_text())


def accepts(task, group, output, citations):
    spec = read(ROOT / 'datasets/workflow-v15/tasks' / task / 'tests/gold.json')[group][output]
    return SCORER.supported(citations, spec['evidence'], spec['context_evidence_allowed'])


def test_reconstruction_and_scorer_identity(tmp_path):
    actual = construct(tmp_path)
    assert actual == load(ROOT, 'workflow-v15')
    old = load(ROOT, 'workflow-v14')
    for key in ('scorer_version', 'scorer_sha256', 'sql_worker_sha256'):
        assert actual[key] == old[key]
    for file in tmp_path.rglob('*'):
        if file.is_file():
            assert file.read_bytes() == (ROOT / 'datasets/workflow-v15' / file.relative_to(tmp_path)).read_bytes()


def test_compatibility_distinguishes_public_clarifications():
    review = read(ROOT / 'config/workflow-contract-adjudication.json')
    changed = set(review['model_visible_changed_tasks'])
    assert changed == {'b08', 'c03', 'c06', 'c08', 'c09', 'c10'}
    manifest = load(ROOT, 'workflow-v15')
    assert manifest['contract_revision']['model_visible_changed_tasks'] == sorted(changed)
    for key in manifest['tasks']:
        _, before, old = load(ROOT, 'workflow-v14', key)
        _, after, new = load(ROOT, 'workflow-v15', key)
        assert (old / 'environment/data.sqlite').read_bytes() == (new / 'environment/data.sqlite').read_bytes()
        for file in old.rglob('*'):
            if not file.is_file():
                continue
            relative = file.relative_to(old).as_posix()
            if relative in ('authoring.json', 'tests/gold.json'):
                continue
            if key in changed and relative == 'environment/output_contract.json':
                continue
            if key == 'c10' and relative in ('solution/forecast_bounds.sql', 'solution/solve.sh'):
                continue
            assert file.read_bytes().replace(before['task_id'].encode(), after['task_id'].encode()) == (new / relative).read_bytes(), (key, relative)


@pytest.mark.parametrize('task,group,output,good,bad', [
    ('a08', 'tables', 'income_model', ['a08:s01', 'a08:s02'], ['a08:s02']),
    ('a10', 'tables', 'income_model', ['a10:s01', 'a10:s03'], ['a10:s03']),
    ('b07', 'tables', 'booking_ratios', ['b07:s01', 'b07:s03'], ['b07:s03']),
    ('c06', 'tables', 'geographic_currency', ['c06:s01', 'c06:s03'], ['c06:s03']),
    ('c06', 'tables', 'consolidated_currency_bridge', ['c06:s01', 'c06:s02'], ['c06:s02']),
    ('c07', 'tables', 'financial_versions', ['c07:s01', 'c07:s02', 'c07:s03'], ['c07:s03']),
    ('c07', 'claims', 'claim_1', ['c07:s01', 'c07:s03'], ['c07:s03']),
    ('c07', 'claims', 'claim_3', ['c07:s01', 'c07:s02'], ['c07:s01']),
])
def test_sufficient_core_relevant_context_and_missing_core(task, group, output, good, bad):
    assert accepts(task, group, output, good)
    assert not accepts(task, group, output, bad)
    assert not accepts(task, group, output, good + [task + ':s99'])


@pytest.mark.parametrize('task,group,output,citations', [
    ('a03', 'claims', 'claim_2', ['a03:s03']),
    ('a09', 'claims', 'claim_1', ['a09:s03']),
    ('b10', 'tables', 'consolidated_cash_bridge', ['b10:s02']),
    ('c04', 'claims', 'claim_3', ['c04:s02']),
    ('c08', 'tables', 'share_basis', ['c08:s02']),
    ('c10', 'tables', 'forecast_bounds', ['c10:s03']),
    ('b07', 'claims', 'claim_1', ['b07:s02', 'b07:s03']),
    ('c03', 'tables', 'gross_to_net', ['c03:s01', 'c03:s02']),
])
def test_missing_numerical_scope_and_irrelevant_evidence_stay_rejected(task, group, output, citations):
    assert not accepts(task, group, output, citations)


def reference_forecast(connection):
    sql = (ROOT / 'datasets/workflow-v15/tasks/c10/solution/forecast_bounds.sql').read_text()
    return [tuple(row) for row in connection.execute(sql)]


def test_forecast_uses_independent_reported_operating_baseline():
    old = ROOT / 'datasets/workflow-v14/tasks/c10'
    new = ROOT / 'datasets/workflow-v15/tasks/c10'
    gold = read(new / 'tests/gold.json')
    control = next(r for r in gold['controls'] if r['name'] == 'independent_disclosure_discrepancy')
    with sqlite3.connect(':memory:') as connection:
        with sqlite3.connect((old / 'tests/data.sqlite').as_uri() + '?mode=ro', uri=True) as source:
            source.backup(connection)
        original = reference_forecast(connection)
        connection.execute('UPDATE annual_margin SET revenue_usd_thousand=revenue_usd_thousand+17 WHERE year=2025')
        changed_revenue = reference_forecast(connection)
        assert all(a[3] != b[3] and a[5] == b[5] for a, b in zip(original, changed_revenue))
        assert [list(row) for row in changed_revenue] == control['tables']['forecast_bounds']
        connection.execute('UPDATE annual_margin SET operating_income_usd_thousand=operating_income_usd_thousand+17 WHERE year=2025')
        changed_reported_income = reference_forecast(connection)
        assert all(a[3] == b[3] and a[5] != b[5] for a, b in zip(changed_revenue, changed_reported_income))
    assert gold['controls'][-1]['changes'] == read(old / 'tests/gold.json')['controls'][-1]['changes']


def test_three_part_cc_decomposition_and_independent_residual_survive():
    task = ROOT / 'datasets/workflow-v15/tasks/c06'
    gold = read(task / 'tests/gold.json')
    cols = list(gold['tables']['consolidated_currency_bridge']['columns'])
    for rows in [gold['tables']['consolidated_currency_bridge']['rows']] + [c['tables']['consolidated_currency_bridge'] for c in gold['controls']]:
        for row in rows:
            values = dict(zip(cols, row))
            assert values['cc_change_usd_million'] + values['fx_effect_usd_million'] + values['hedging_change_usd_million'] == pytest.approx(values['reported_change_usd_million'])
    discrepancy = next(c for c in gold['controls'] if c['name'] == 'independent_disclosure_discrepancy')
    assert discrepancy['tables']['consolidated_currency_bridge'][0][cols.index('cc_disclosure_residual_usd_million')] == 17


def test_empty_litigation_contribution_is_not_a_source_observation():
    task = ROOT / 'datasets/workflow-v15/tasks/c03'
    sql = (task / 'solution/net_income_reconciliation.sql').read_text()
    with sqlite3.connect((task / 'tests/data.sqlite').as_uri() + '?mode=ro', uri=True) as connection:
        assert connection.execute("SELECT count(*) FROM net_income_reconciliation WHERE period='Q4FY2024' AND measure='litigation'").fetchone()[0] == 0
        result = connection.execute(sql)
        columns = [column[0] for column in result.description]
        rows = [dict(zip(columns, row)) for row in result]
        row = next(row for row in rows if row['period'] == 'Q4FY2024')
        assert row['litigation_adjustment_usd_million'] == 0
    definition = read(task / 'environment/output_contract.json')['definitions']['net_income_reconciliation']
    assert 'without asserting a separately observed zero' in definition
