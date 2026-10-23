import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import types

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]
V12 = ROOT / 'datasets/workflow-v12'
V13 = ROOT / 'datasets/workflow-v13'
sys.path.insert(0, str(ROOT / 'scripts'))
from build_workflow_measurement_revision import DATASET, REVIEW, construct


def read(path):
    return json.loads(path.read_text())


def table_rows(task, database, name):
    with sqlite3.connect(database) as connection:
        cursor = connection.execute((task / 'solution' / (name + '.sql')).read_text())
        return [dict(zip((column[0] for column in cursor.description), row)) for row in cursor.fetchall()]


def synthetic_database(task, mutate):
    temp = tempfile.TemporaryDirectory()
    database = Path(temp.name) / 'data.sqlite'
    shutil.copyfile(task / 'tests/data.sqlite', database)
    with sqlite3.connect(database) as connection:
        mutate(connection)
    return temp, database


def test_revision_is_separate_and_preserves_financial_inputs_and_gold_targets():
    previous = load(ROOT, 'workflow-v12')
    manifest = read(V13 / 'manifest.json')
    assert manifest['dataset_id'] == DATASET
    assert manifest['prior_catalog'] == previous['manifest_id']
    for field in ('scorer_version', 'scorer_sha256', 'sql_worker_sha256'):
        assert manifest[field] == previous[field]
    assert manifest['measurement_revision']['new_inference'] is False
    assert manifest['measurement_revision']['human_review'] == 'pending'

    review = read(ROOT / REVIEW)
    for key in previous['tasks']:
        old_task = V12 / 'tasks' / key
        new_task = V13 / 'tasks' / key
        old_gold = read(old_task / 'tests/gold.json')
        new_gold = read(new_task / 'tests/gold.json')
        expected_gold = copy.deepcopy(old_gold)
        expected_gold.update(task_id=manifest['tasks'][key]['task_id'], hashes=new_gold['hashes'])
        for name, evidence in review['additional_context_evidence'].get(key, {}).items():
            target = expected_gold['claims'][name]['context_evidence_allowed'] if name in expected_gold['claims'] else expected_gold['tables'][name]['context_evidence_allowed']
            target.extend(item for item in evidence if item not in target)
        assert new_gold == expected_gold
        expected_definitions = copy.deepcopy(read(old_task / 'environment/output_contract.json')['definitions'])
        for table, addendum in review['definitions'].get(key, {}).items():
            expected_definitions[table] = expected_definitions[table].rstrip() + ' ' + addendum.strip()
        expected_definitions.update(review.get('new_definitions', {}).get(key, {}))
        assert read(new_task / 'environment/output_contract.json')['definitions'] == expected_definitions
        for relative in ('tests/data.sqlite', 'tests/gold.json', 'solution'):
            if relative == 'tests/gold.json':
                continue
            old_path, new_path = old_task / relative, new_task / relative
            if old_path.is_dir():
                for old_file in old_path.rglob('*'):
                    if old_file.is_file():
                        assert old_file.read_bytes().replace(previous['tasks'][key]['task_id'].encode(), manifest['tasks'][key]['task_id'].encode()) == (new_path / old_file.relative_to(old_path)).read_bytes()
            else:
                assert old_path.read_bytes() == new_path.read_bytes()

    assert read(V13 / 'tasks/a03/tests/gold.json')['claims']['claim_2'] == read(V12 / 'tasks/a03/tests/gold.json')['claims']['claim_2']
    costco = read(V13 / 'tasks/a05/tests/gold.json')
    assert costco['tables']['income_model']['evidence'] == [['a05:s01']]
    assert costco['tables']['income_model']['context_evidence_allowed'] == ['a05:s02']
    assert costco['claims']['claim_1']['evidence'] == [['a05:s01']]
    assert costco['claims']['claim_1']['context_evidence_allowed'] == ['a05:s02']


def test_construct_reproduces_materialized_bundle(tmp_path):
    expected = construct(tmp_path)
    actual = read(V13 / 'manifest.json')
    assert actual == expected
    for path in tmp_path.rglob('*'):
        if path.is_file():
            assert path.read_bytes() == (V13 / path.relative_to(tmp_path)).read_bytes()


def test_a03_components_rebuild_margins_and_signed_residuals():
    task = V12 / 'tasks/a03'
    baseline_expense = table_rows(task, task / 'tests/data.sqlite', 'expense_model')

    def change_expense(connection):
        result = connection.execute("UPDATE expense_reconciliation SET amount_usd_thousand=amount_usd_thousand+17 WHERE period='Q4FY2025' AND measure='gaap'")
        assert result.rowcount == 1

    temp, database = synthetic_database(task, change_expense)
    try:
        changed_expense = table_rows(task, database, 'expense_model')
        prior = {row['period']: row for row in baseline_expense}
        current = {row['period']: row for row in changed_expense}
        assert current['Q4FY2025']['prior_residual_usd_thousand'] - prior['Q4FY2025']['prior_residual_usd_thousand'] == 17
        assert current['Q4FY2025']['new_residual_usd_thousand'] - prior['Q4FY2025']['new_residual_usd_thousand'] == 17
        assert current['9MFY2025']['prior_residual_usd_thousand'] - prior['9MFY2025']['prior_residual_usd_thousand'] == -17
        assert current['9MFY2025']['new_residual_usd_thousand'] - prior['9MFY2025']['new_residual_usd_thousand'] == -17
    finally:
        temp.cleanup()

    def change_components(connection):
        r = connection.execute("UPDATE operations SET amount_usd_thousand=amount_usd_thousand+17 WHERE period='Q4FY2025' AND measure='reserve_income'")
        c = connection.execute("UPDATE operations SET amount_usd_thousand=amount_usd_thousand+5 WHERE period='Q4FY2025' AND measure='distribution'")
        assert r.rowcount == c.rowcount == 1

    temp, database = synthetic_database(task, change_components)
    try:
        base = next(row for row in table_rows(task, task / 'tests/data.sqlite', 'operating_margins') if row['period'] == 'Q4FY2025')
        changed = next(row for row in table_rows(task, database, 'operating_margins') if row['period'] == 'Q4FY2025')
        assert changed['revenue_usd_thousand'] == base['revenue_usd_thousand'] + 17
        assert changed['rldc_usd_thousand'] == base['rldc_usd_thousand'] + 12
        assert changed['revenue_residual_usd_thousand'] == base['revenue_residual_usd_thousand'] + 17
        assert changed['cost_residual_usd_thousand'] == base['cost_residual_usd_thousand'] + 5
        assert changed['rldc_margin_pct'] == 100.0 * changed['rldc_usd_thousand'] / changed['revenue_usd_thousand']
        with sqlite3.connect(database) as connection:
            adjusted_ebitda = connection.execute("SELECT amount_usd_thousand FROM operations WHERE period='Q4FY2025' AND measure='adjusted_ebitda'").fetchone()[0]
        assert changed['adjusted_ebitda_margin_pct'] == 100.0 * adjusted_ebitda / changed['rldc_usd_thousand']
        assert changed['revenue_residual_usd_thousand'] != 0
        assert changed['cost_residual_usd_thousand'] != 0
        assert changed['rldc_margin_pct'] != 100.0 * changed['rldc_usd_thousand'] / (base['revenue_usd_thousand'])
    finally:
        temp.cleanup()


def test_a05_reconstructed_income_and_residual_propagate_through_36_weeks():
    task = V12 / 'tasks/a05'
    source = task / 'tests/data.sqlite'
    baseline = table_rows(task, source, 'income_model')

    def change_component(connection):
        result = connection.execute('UPDATE income SET net_sales_usd_million=net_sales_usd_million+17 WHERE fiscal_year=2025 AND weeks=16')
        assert result.rowcount == 1

    temp, database = synthetic_database(task, change_component)
    try:
        changed = table_rows(task, database, 'income_model')
        before = {(row['fiscal_year'], row['weeks']): row for row in baseline}
        after = {(row['fiscal_year'], row['weeks']): row for row in changed}
        for weeks, delta in ((16, 17), (36, -17), (52, 0)):
            key = (2025, weeks)
            assert after[key]['operating_income_usd_million'] - before[key]['operating_income_usd_million'] == delta
            assert after[key]['residual_usd_million'] - before[key]['residual_usd_million'] == delta
        assert after[(2025, 16)]['residual_usd_million'] == 17
        assert after[(2025, 36)]['residual_usd_million'] == -17
        assert after[(2025, 16)]['operating_income_usd_million'] != after[(2025, 16)]['residual_usd_million']
    finally:
        temp.cleanup()


def test_a06_reconstructs_each_stage_and_preserves_cumulative_chain():
    task = V12 / 'tasks/a06'
    source = task / 'tests/data.sqlite'
    baseline_income = table_rows(task, source, 'income_model')
    baseline_bridge = table_rows(task, source, 'adjustment_bridge')

    def change_q3_revenue(connection):
        result = connection.execute('UPDATE income SET revenue_usd_million=revenue_usd_million+17 WHERE fiscal_year=2026 AND months=3')
        assert result.rowcount == 1

    temp, database = synthetic_database(task, change_q3_revenue)
    try:
        changed_income = table_rows(task, database, 'income_model')
        changed_bridge = table_rows(task, database, 'adjustment_bridge')
        before_income = {(row['fiscal_year'], row['months']): row for row in baseline_income}
        after_income = {(row['fiscal_year'], row['months']): row for row in changed_income}
        before_bridge = {(row['fiscal_year'], row['months']): row for row in baseline_bridge}
        after_bridge = {(row['fiscal_year'], row['months']): row for row in changed_bridge}
        for months, delta in ((3, 17), (6, -17), (9, 0)):
            key = (2026, months)
            for field in ('gaap_operating_income_usd_million', 'adjusted_operating_income_usd_million', 'adjusted_cc_operating_income_usd_million'):
                assert after_income[key][field] - before_income[key][field] == delta
            for field in ('gaap_residual_usd_million', 'adjusted_residual_usd_million', 'cc_residual_usd_million'):
                assert after_bridge[key][field] - before_bridge[key][field] == delta
        q3 = after_income[(2026, 3)]
        h1 = after_income[(2026, 6)]
        assert q3['gaap_margin_pct'] == 100.0 * q3['gaap_operating_income_usd_million'] / q3['revenue_usd_million']
        assert q3['adjusted_margin_pct'] == 100.0 * q3['adjusted_operating_income_usd_million'] / q3['revenue_usd_million']
        assert h1['gaap_operating_income_usd_million'] != before_income[(2026, 6)]['gaap_operating_income_usd_million']
        assert after_bridge[(2026, 3)]['gaap_residual_usd_million'] == before_bridge[(2026, 3)]['gaap_residual_usd_million'] + 17
        assert after_bridge[(2026, 6)]['gaap_residual_usd_million'] == before_bridge[(2026, 6)]['gaap_residual_usd_million'] - 17
    finally:
        temp.cleanup()


def test_a03_independent_reported_expenses_and_totals_move_only_residuals():
    task = V12 / 'tasks/a03'
    source = task / 'tests/data.sqlite'
    baseline_expense = table_rows(task, source, 'expense_model')

    def change_reported_expenses(connection):
        prior = connection.execute("UPDATE expense_reconciliation SET amount_usd_thousand=amount_usd_thousand+13 WHERE period='Q4FY2025' AND measure='prior_definition'")
        new = connection.execute("UPDATE expense_reconciliation SET amount_usd_thousand=amount_usd_thousand+19 WHERE period='Q4FY2025' AND measure='new_definition'")
        assert prior.rowcount == new.rowcount == 1

    temp, database = synthetic_database(task, change_reported_expenses)
    try:
        changed = table_rows(task, database, 'expense_model')
        before = {row['period']: row for row in baseline_expense}
        after = {row['period']: row for row in changed}
        for period, prior_delta, new_delta in (('Q4FY2025', -13, -19), ('9MFY2025', 13, 19)):
            for field in ('prior_adjusted_usd_thousand', 'new_adjusted_usd_thousand'):
                assert after[period][field] == before[period][field]
            assert after[period]['prior_residual_usd_thousand'] - before[period]['prior_residual_usd_thousand'] == prior_delta
            assert after[period]['new_residual_usd_thousand'] - before[period]['new_residual_usd_thousand'] == new_delta
    finally:
        temp.cleanup()

    baseline_margins = table_rows(task, source, 'operating_margins')

    def change_reported_totals(connection):
        revenue = connection.execute("UPDATE operations SET amount_usd_thousand=amount_usd_thousand+23 WHERE period='Q4FY2025' AND measure='total_revenue'")
        costs = connection.execute("UPDATE operations SET amount_usd_thousand=amount_usd_thousand+29 WHERE period='Q4FY2025' AND measure='total_costs'")
        assert revenue.rowcount == costs.rowcount == 1

    temp, database = synthetic_database(task, change_reported_totals)
    try:
        changed = table_rows(task, database, 'operating_margins')
        before = {row['period']: row for row in baseline_margins}
        after = {row['period']: row for row in changed}
        for field in ('revenue_usd_thousand', 'rldc_usd_thousand', 'rldc_margin_pct', 'adjusted_ebitda_margin_pct'):
            assert after['Q4FY2025'][field] == before['Q4FY2025'][field]
        assert after['Q4FY2025']['revenue_residual_usd_thousand'] - before['Q4FY2025']['revenue_residual_usd_thousand'] == -23
        assert after['Q4FY2025']['cost_residual_usd_thousand'] - before['Q4FY2025']['cost_residual_usd_thousand'] == -29
    finally:
        temp.cleanup()


def test_a05_reported_operating_income_change_moves_only_residual():
    task = V12 / 'tasks/a05'
    source = task / 'tests/data.sqlite'
    baseline = table_rows(task, source, 'income_model')

    def change_reported_income(connection):
        result = connection.execute('UPDATE income SET operating_income_usd_million=operating_income_usd_million+23 WHERE fiscal_year=2025 AND weeks=16')
        assert result.rowcount == 1

    temp, database = synthetic_database(task, change_reported_income)
    try:
        changed = table_rows(task, database, 'income_model')
        before = {(row['fiscal_year'], row['weeks']): row for row in baseline}
        after = {(row['fiscal_year'], row['weeks']): row for row in changed}
        for weeks, delta in ((16, -23), (36, 23), (52, 0)):
            key = (2025, weeks)
            for field in ('merchandise_gross_profit_usd_million', 'merchandise_gross_margin_pct', 'operating_income_usd_million'):
                assert after[key][field] == before[key][field]
            assert after[key]['residual_usd_million'] - before[key]['residual_usd_million'] == delta
    finally:
        temp.cleanup()


def test_a06_independent_reported_bases_move_only_their_residuals():
    task = V12 / 'tasks/a06'
    source = task / 'tests/data.sqlite'
    baseline_income = table_rows(task, source, 'income_model')
    baseline_bridge = table_rows(task, source, 'adjustment_bridge')

    def change_reported_bases(connection):
        gaap = connection.execute('UPDATE income SET operating_income_usd_million=operating_income_usd_million+23 WHERE fiscal_year=2026 AND months=3')
        adjusted = connection.execute('UPDATE adjustments SET reported_adjusted_usd_million=reported_adjusted_usd_million+29 WHERE fiscal_year=2026 AND months=3')
        cc = connection.execute('UPDATE adjustments SET reported_adjusted_cc_usd_million=reported_adjusted_cc_usd_million+31 WHERE fiscal_year=2026 AND months=3')
        assert gaap.rowcount == adjusted.rowcount == cc.rowcount == 1

    temp, database = synthetic_database(task, change_reported_bases)
    try:
        changed_income = table_rows(task, database, 'income_model')
        changed_bridge = table_rows(task, database, 'adjustment_bridge')
        before_income = {(row['fiscal_year'], row['months']): row for row in baseline_income}
        after_income = {(row['fiscal_year'], row['months']): row for row in changed_income}
        before_bridge = {(row['fiscal_year'], row['months']): row for row in baseline_bridge}
        after_bridge = {(row['fiscal_year'], row['months']): row for row in changed_bridge}
        for key in before_income:
            for field in ('gaap_operating_income_usd_million', 'adjusted_operating_income_usd_million', 'adjusted_cc_operating_income_usd_million', 'gaap_margin_pct', 'adjusted_margin_pct'):
                assert after_income[key][field] == before_income[key][field]
        for months, gaap_delta, adjusted_delta, cc_delta in ((3, -23, -29, -31), (6, 23, 29, 31), (9, 0, 0, 0)):
            key = (2026, months)
            assert after_bridge[key]['gaap_residual_usd_million'] - before_bridge[key]['gaap_residual_usd_million'] == gaap_delta
            assert after_bridge[key]['adjusted_residual_usd_million'] - before_bridge[key]['adjusted_residual_usd_million'] == adjusted_delta
            assert after_bridge[key]['cc_residual_usd_million'] - before_bridge[key]['cc_residual_usd_million'] == cc_delta
    finally:
        temp.cleanup()


def test_a06_signed_adjustment_and_currency_changes_propagate_downstream():
    task = V12 / 'tasks/a06'
    source = task / 'tests/data.sqlite'
    baseline_income = table_rows(task, source, 'income_model')
    baseline_bridge = table_rows(task, source, 'adjustment_bridge')

    def change_signed_adjustment(connection):
        result = connection.execute('UPDATE adjustments SET phonepe_sbc_usd_million=phonepe_sbc_usd_million+11 WHERE fiscal_year=2026 AND months=3')
        assert result.rowcount == 1

    temp, database = synthetic_database(task, change_signed_adjustment)
    try:
        changed_income = table_rows(task, database, 'income_model')
        changed_bridge = table_rows(task, database, 'adjustment_bridge')
        before = {(row['fiscal_year'], row['months']): row for row in baseline_income}
        after = {(row['fiscal_year'], row['months']): row for row in changed_income}
        before_bridge = {(row['fiscal_year'], row['months']): row for row in baseline_bridge}
        after_bridge = {(row['fiscal_year'], row['months']): row for row in changed_bridge}
        for months, delta in ((3, 11), (6, -11), (9, 0)):
            key = (2026, months)
            assert after[key]['gaap_operating_income_usd_million'] == before[key]['gaap_operating_income_usd_million']
            assert after[key]['adjusted_operating_income_usd_million'] - before[key]['adjusted_operating_income_usd_million'] == delta
            assert after[key]['adjusted_cc_operating_income_usd_million'] - before[key]['adjusted_cc_operating_income_usd_million'] == delta
            assert after_bridge[key]['gaap_residual_usd_million'] == before_bridge[key]['gaap_residual_usd_million']
            assert after_bridge[key]['adjusted_residual_usd_million'] - before_bridge[key]['adjusted_residual_usd_million'] == delta
            assert after_bridge[key]['cc_residual_usd_million'] - before_bridge[key]['cc_residual_usd_million'] == delta
    finally:
        temp.cleanup()

    def change_currency_bridge(connection):
        result = connection.execute('UPDATE adjustments SET adjusted_currency_usd_million=adjusted_currency_usd_million+13 WHERE fiscal_year=2026 AND months=3')
        assert result.rowcount == 1

    temp, database = synthetic_database(task, change_currency_bridge)
    try:
        changed_income = table_rows(task, database, 'income_model')
        changed_bridge = table_rows(task, database, 'adjustment_bridge')
        before = {(row['fiscal_year'], row['months']): row for row in baseline_income}
        after = {(row['fiscal_year'], row['months']): row for row in changed_income}
        before_bridge = {(row['fiscal_year'], row['months']): row for row in baseline_bridge}
        after_bridge = {(row['fiscal_year'], row['months']): row for row in changed_bridge}
        for months, delta in ((3, 13), (6, -13), (9, 0)):
            key = (2026, months)
            assert after[key]['gaap_operating_income_usd_million'] == before[key]['gaap_operating_income_usd_million']
            assert after[key]['adjusted_operating_income_usd_million'] == before[key]['adjusted_operating_income_usd_million']
            assert after[key]['adjusted_cc_operating_income_usd_million'] - before[key]['adjusted_cc_operating_income_usd_million'] == delta
            assert after_bridge[key]['adjusted_residual_usd_million'] == before_bridge[key]['adjusted_residual_usd_million']
            assert after_bridge[key]['cc_residual_usd_million'] - before_bridge[key]['cc_residual_usd_million'] == delta
    finally:
        temp.cleanup()


def test_a05_context_citation_does_not_become_sufficient_alone_and_a03_claim_is_unchanged():
    package_path = V13 / 'tasks/a05/tests/workpaperbench'
    module_path = package_path / 'workflow_grading.py'
    prior_package = sys.modules.get('workpaperbench')
    prior_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    package = types.ModuleType('workpaperbench')
    package.__path__ = [str(package_path)]
    sys.modules['workpaperbench'] = package
    try:
        spec = importlib.util.spec_from_file_location('workpaperbench.workflow_grading', module_path)
        scorer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scorer)
    finally:
        sys.modules.pop('workpaperbench.workflow_grading', None)
        sys.modules.pop('workpaperbench.grading', None)
        sys.modules['workpaperbench'] = prior_package
        sys.dont_write_bytecode = prior_bytecode
    gold = read(V13 / 'tasks/a05/tests/gold.json')
    for name in ('income_model', 'claim_1'):
        item = gold['tables'][name] if name == 'income_model' else gold['claims'][name]
        assert scorer.supported(['a05:s01'], item['evidence'], item['context_evidence_allowed'])
        assert scorer.supported(['a05:s01', 'a05:s02'], item['evidence'], item['context_evidence_allowed'])
        assert not scorer.supported(['a05:s02'], item['evidence'], item['context_evidence_allowed'])
    old_claim = read(V12 / 'tasks/a03/tests/gold.json')['claims']['claim_2']
    new_claim = read(V13 / 'tasks/a03/tests/gold.json')['claims']['claim_2']
    assert new_claim == old_claim
    assert not scorer.supported(['a03:s03'], new_claim['evidence'], new_claim['context_evidence_allowed'])
