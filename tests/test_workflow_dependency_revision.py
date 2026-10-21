import copy
import json
from pathlib import Path
import platform
import sqlite3
import shutil
import sys
import types

import pytest

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from workflow_dependency_cases import AUDIT_TARGETS, TARGETS, artifacts, validate_verdict


def read(path):
    return json.loads(path.read_text())


def assert_unchanged_rows(gold, table, rows):
    spec = gold['tables'][table]
    assert len(rows) == len(spec['rows'])
    for actual, expected in zip(sorted(rows), sorted(spec['rows'])):
        for column, value, target in zip(spec['columns'].values(), actual, expected):
            if column['type'] == 'real':
                assert value == pytest.approx(target, abs=column['tolerance'], rel=0)
            else:
                assert value == target


def test_new_catalog_preserves_originals_references_splits_and_historical_controls():
    prior, current = load(ROOT, 'workflow-v10'), load(ROOT, 'workflow-v11')
    assert current['prior_catalog'] == prior['manifest_id']
    assert current['scorer_version'] == prior['scorer_version'] == 'workflow-1.2.1'
    assert current['scorer_sha256'] == prior['scorer_sha256']
    assert current['sql_worker_sha256'] == prior['sql_worker_sha256']
    assert set(prior['tasks']) == set(current['tasks'])
    for key in current['tasks']:
        _, before, old = load(ROOT, 'workflow-v10', key)
        _, after, new = load(ROOT, 'workflow-v11', key)
        assert (before['split'], before['source_group']) == (after['split'], after['source_group'])
        gold_before, gold_after = read(old / 'tests/gold.json'), read(new / 'tests/gold.json')
        expected = copy.deepcopy(gold_before)
        expected.update(task_id=after['task_id'], hashes=gold_after['hashes'])
        if key in TARGETS:
            expected['controls'].append(gold_after['controls'][-1])
            assert gold_after['controls'][-1]['origin'] == 'authored_synthetic_counterfactual'
        assert expected == gold_after
        for path in old.rglob('*'):
            if not path.is_file():
                continue
            relative = path.relative_to(old)
            if str(relative) == 'tests/gold.json' or (key in TARGETS and str(relative) == 'authoring.json'):
                continue
            assert path.read_bytes().replace(before['task_id'].encode(), after['task_id'].encode()) == (new / relative).read_bytes()


def test_independently_calculated_subscription_cost_and_aggregate_bridge():
    task = ROOT / 'datasets/workflow-v11/tasks/c01'
    gold = read(task / 'tests/gold.json')
    control = gold['controls'][-1]
    with sqlite3.connect(task / 'tests' / control['database']) as db:
        costs = dict(db.execute("SELECT category,amount FROM costs WHERE period_end='2024-12-31' AND months=12"))
        revenues = dict(db.execute("SELECT category,amount FROM revenues WHERE period_end='2024-12-31' AND months=12"))
    assert costs['Subscription and services-based costs'] == 1136813
    assert costs['Total cost of revenue'] == 15233017
    assert revenues['Subscription and services-based revenue'] == 7164799
    expected_profit = 7164799 - 1136813
    prior_profit = 5944842 - 1075129
    row = next(r for r in control['tables']['profit_bridge'] if r[0] == 'subscription')
    assert row == ['subscription', prior_profit, expected_profit, expected_profit - prior_profit]
    assert expected_profit == 6027986
    assert expected_profit - prior_profit == 1158273
    aggregate_change = (24121053 - 15233017) - (21915623 - 14410737)
    assert aggregate_change == 1383150
    reconciliation = dict(zip(gold['tables']['reconciliation']['columns'], control['tables']['reconciliation'][0]))
    assert reconciliation['gross_profit_change_usd_thousand'] == aggregate_change
    assert sum(row[3] for row in control['tables']['profit_bridge']) == aggregate_change
    assert reconciliation['revenue_change_usd_thousand'] == 24121053 - 21915623
    assert reconciliation['gross_profit_residual_usd_thousand'] == 0
    assert reconciliation['revenue_residual_usd_thousand'] == 0
    assert_unchanged_rows(gold, 'revenue_bridge', control['tables']['revenue_bridge'])


def test_independently_calculated_activity_ratios_use_declared_tolerances():
    task = ROOT / 'datasets/workflow-v11/tasks/b06'
    gold = read(task / 'tests/gold.json')
    control = gold['controls'][-1]
    spec = gold['tables']['consumer_activity']
    row = dict(zip(spec['columns'], next(r for r in control['tables']['consumer_activity'] if r[0] == 2025)))
    assert (row['trips_million'], row['mapcs_million'], row['months']) == (3751 + 202, 202, 3)
    for column, expected in [('quarterly_trips_per_monthly_consumer', 3953 / 202),
                             ('monthly_trips_per_monthly_consumer', 3953 / (202 * 3))]:
        assert row[column] == pytest.approx(expected, abs=spec['columns'][column]['tolerance'], rel=0)
    for table in ('segment_metrics', 'corporate_bridge'):
        assert_unchanged_rows(gold, table, control['tables'][table])
    assert control['tables']['consumer_activity'][0] == pytest.approx(spec['rows'][0], abs=1e-6, rel=0)


def test_additional_volume_and_cost_controls_preserve_financial_meaning():
    b03 = read(ROOT / 'datasets/workflow-v11/tasks/b03/tests/gold.json')
    control = b03['controls'][-1]
    spec = b03['tables']['spot_revenue_proxy']
    row = dict(zip(spec['columns'], next(r for r in control['tables']['spot_revenue_proxy'] if r[0] == 'consumer')))
    assert row['spot_volume_usd_billion'] == 56 + 10
    assert row['revenue_usd_million'] == 733.9
    assert row['apparent_revenue_to_spot_pct'] == pytest.approx(100 * 733.9 / 66000, abs=1e-6, rel=0)
    for table in ('annual_revenue_bridge', 'usdc_booked_ratio'):
        assert_unchanged_rows(b03, table, control['tables'][table])
    c04 = read(ROOT / 'datasets/workflow-v11/tasks/c04/tests/gold.json')
    spec = c04['tables']['company_margin_bridge']
    control = c04['controls'][-1]
    for period, revenue, gaap, adjusted in [('Q4FY2025', 8806, 3896 + 100, 3721 + 100),
                                           ('FY2025', 32791, 13894 + 100, 13389 + 100)]:
        row = dict(zip(spec['columns'], next(r for r in control['tables']['company_margin_bridge'] if r[0] == period)))
        assert row['gaap_operating_income_usd_million'] == revenue - gaap
        assert row['adjusted_operating_income_usd_million'] == revenue - adjusted
        assert row['gaap_margin_pct'] == pytest.approx(100 * (revenue - gaap) / revenue, abs=1e-6, rel=0)
        assert row['adjusted_margin_pct'] == pytest.approx(100 * (revenue - adjusted) / revenue, abs=1e-6, rel=0)
        original = dict(zip(spec['columns'], next(r for r in spec['rows'] if r[0] == period)))
        assert row['expense_residual_usd_million'] == original['expense_residual_usd_million'] == 1
    for table in ('regional_attribution', 'worldwide_reconciliation'):
        assert_unchanged_rows(c04, table, control['tables'][table])


@pytest.mark.skipif(platform.system() != 'Linux', reason='Full SQL worker resource limits require Linux')
@pytest.mark.parametrize('key', TARGETS)
@pytest.mark.parametrize('case', ['reference', 'alternative', 'frozen'])
def test_complete_submission_to_verdict_dependency_regression(tmp_path, key, case):
    for dataset in ('workflow-v10', 'workflow-v11'):
        _, _, task = load(ROOT, dataset, key)
        directory = tmp_path / dataset
        directory.mkdir()
        files = artifacts(task, case)
        reference = artifacts(task)
        if case != 'reference':
            assert {name for name in files if files[name] != reference[name]} == {TARGETS[key][0] + '.sql'}
        for name, raw in files.items():
            (directory / name).write_bytes(raw)
        trusted = tmp_path / (dataset + '-trusted')
        shutil.copytree(task / 'tests', trusted)
        path = trusted / 'workpaperbench/workflow_grading.py'
        module = types.ModuleType('workpaperbench.dependency_test')
        module.__file__, module.__package__ = str(path), 'workpaperbench'
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
        verdict = module.grade(directory, trusted)
        validate_verdict(verdict, key, case, dataset == 'workflow-v11')
