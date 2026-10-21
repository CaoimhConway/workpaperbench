import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def scorer():
    module = importlib.util.spec_from_file_location('workpaperbench.contract_revision',
        ROOT / 'config/scorers/workflow-1.2.1.py')
    result = importlib.util.module_from_spec(module)
    module.loader.exec_module(result)
    return result


def test_revision_preserves_sources_sql_financial_targets_and_all_controls():
    prior, current = load(ROOT, 'workflow-v9'), load(ROOT, 'workflow-v10')
    assert current['prior_catalog'] == prior['manifest_id']
    assert current['scorer_version'] == 'workflow-1.2.1'
    assert set(current['tasks']) == set(prior['tasks'])
    for key in current['tasks']:
        _, before_spec, old = load(ROOT, 'workflow-v9', key)
        _, after_spec, new = load(ROOT, 'workflow-v10', key)
        assert before_spec['split'] == after_spec['split']
        assert before_spec['source_group'] == after_spec['source_group']
        assert {p.relative_to(old) for p in old.rglob('*') if p.is_file()} == {
            p.relative_to(new) for p in new.rglob('*') if p.is_file()}
        special = {'tests/gold.json', 'authoring.json',
                   'tests/workpaperbench/workflow_grading.py',
                   'tests/workpaperbench/workflow_sql_worker.py'}
        if key in ('b02', 'b06', 'c01'):
            special.add('environment/output_contract.json')
        for path in old.rglob('*'):
            relative = path.relative_to(old).as_posix()
            if not path.is_file() or relative in special:
                continue
            expected = path.read_bytes().replace(('workflow-v9-' + key).encode(),
                                                 ('workflow-v10-' + key).encode())
            assert expected == (new / relative).read_bytes(), (key, relative)
        before, after = read(old / 'tests/gold.json'), read(new / 'tests/gold.json')
        expected = copy.deepcopy(before)
        expected.update(task_id='workflow-v10-' + key, scorer_version='workflow-1.2.1',
                        hashes=after['hashes'])
        if key == 'c01':
            expected['tables']['reconciliation']['keys'] = []
        if key == 'b06':
            expected['claims']['claim_1']['evidence'].append(['b06:s01'])
        assert expected == after
        for table in after['tables'].values():
            assert all(table['columns'][name]['type'] != 'real' for name in table['keys'])
        authoring = read(new / 'authoring.json')
        correction = authoring.pop('contract_correction')
        assert authoring == read(old / 'authoring.json')
        assert correction['prior_task_sha256'] == before_spec['task_sha256']
        assert correction['scorer_version'] == current['scorer_version']
        assert correction['scorer_sha256'] == current['scorer_sha256']
        assert correction['sql_worker_sha256'] == current['sql_worker_sha256']
        for filename, manifest_key in (('workflow_grading.py', 'scorer_sha256'),
                                       ('workflow_sql_worker.py', 'sql_worker_sha256')):
            path = new / 'tests/workpaperbench' / filename
            assert hashlib.sha256(path.read_bytes()).hexdigest() == current[manifest_key]


def test_singleton_reconciliation_applies_tolerance_without_a_numeric_row_identifier():
    task = ROOT / 'datasets/workflow-v10/tasks/c01'
    public = read(task / 'environment/output_contract.json')['tables']['reconciliation']
    spec = read(task / 'tests/gold.json')['tables']['reconciliation']
    assert public['keys'] == spec['keys'] == []
    assert len(spec['rows']) == 1
    column = list(spec['columns']).index('revenue_change_usd_thousand')
    tolerance = spec['columns']['revenue_change_usd_thousand']['tolerance']
    actual = copy.deepcopy(spec['rows'])
    actual[0][column] += 4.656612873077393e-10
    assert actual != spec['rows']
    compare = scorer().comparison_error
    assert compare({'columns': list(spec['columns']), 'rows': actual}, spec, spec['rows']) is None
    actual[0][column] += tolerance * 2
    assert compare({'columns': list(spec['columns']), 'rows': actual}, spec, spec['rows']) is not None
    assert compare({'columns': list(spec['columns']), 'rows': spec['rows'] * 2}, spec, spec['rows']) is not None


def test_explicit_financial_bases_match_retained_discrepancy_targets():
    b02 = ROOT / 'datasets/workflow-v10/tasks/b02'
    before = read(ROOT / 'datasets/workflow-v9/tasks/b02/environment/output_contract.json')
    after = read(b02 / 'environment/output_contract.json')
    definition = after['definitions']['stock_bridge']
    for term in ('reserve_observations', 'reported_assets_usd', 'treasury_fair_value_usd',
                 'current less prior', 'separate from the holdings-based reconstruction'):
        assert term in definition
    before['definitions']['stock_bridge'] = definition
    assert before == after
    gold = read(b02 / 'tests/gold.json')
    control = next(c for c in gold['controls'] if c['name'] == 'independent_disclosure_discrepancy')
    assert control['changes'] == [['treasury_holdings', 0, 'fair_value_usd', 17]]
    assert control['tables']['stock_bridge'] == gold['tables']['stock_bridge']['rows']
    assert control['tables']['qualified_coverage'][0][1] - gold['tables']['qualified_coverage']['rows'][0][1] == 17

    b06 = ROOT / 'datasets/workflow-v10/tasks/b06'
    before = read(ROOT / 'datasets/workflow-v9/tasks/b06/environment/output_contract.json')
    after = read(b06 / 'environment/output_contract.json')
    definition = after['definitions']['corporate_bridge']
    for term in ('reconstructed', 'less platform.adjusted_ebitda_usd_million',
                 'less platform.bookings_usd_million', 'less platform.revenue_usd_million',
                 'divided by summed segment bookings'):
        assert term in definition
    before['definitions']['corporate_bridge'] = definition
    assert before == after
    observations = json.loads((b06 / 'environment/sources.md').read_text().split('Source-derived observations\n\n', 1)[1])
    gold = read(b06 / 'tests/gold.json')
    control = next(c for c in gold['controls'] if c['name'] == 'independent_disclosure_discrepancy')
    values = copy.deepcopy(observations)
    for table, row, column, delta in control['changes']:
        values[table][row][column] += delta
    year = control['tables']['corporate_bridge'][0][0]
    rows = [r for r in values['segments'] if r['year'] == year]
    platform = next(r for r in values['platform'] if r['year'] == year)
    ebitda = sum(r['adjusted_ebitda_usd_million'] for r in rows) + platform['corporate_cost_usd_million']
    bookings = sum(r['bookings_usd_million'] for r in rows)
    revenue = sum(r['revenue_usd_million'] for r in rows)
    expected = [ebitda - platform['adjusted_ebitda_usd_million'],
                bookings - platform['bookings_usd_million'], revenue - platform['revenue_usd_million']]
    assert expected == [51, 17, 34]
    row = dict(zip(gold['tables']['corporate_bridge']['columns'], control['tables']['corporate_bridge'][0]))
    assert row['total_adjusted_ebitda_usd_million'] == ebitda
    assert row['total_ebitda_to_bookings_pct'] == 100 * ebitda / bookings


def test_commission_claim_accepts_sufficient_single_source_without_unknown_citations():
    task = ROOT / 'datasets/workflow-v10/tasks/b06'
    evidence = {r['id']: r for r in read(task / 'environment/evidence.json')}
    assert 'not a uniquely identified commission' in evidence['b06:s01']['text']
    gold = read(task / 'tests/gold.json')
    spec = gold['claims']['claim_1']
    assert spec['verdict'] == 'contradicted'
    assert spec['evidence'] == [['b06:s01', 'b06:s03'], ['b06:s01']]
    support = scorer().supported
    for sufficient in (['b06:s01'], ['b06:s01', 'b06:s03']):
        assert support(sufficient, spec['evidence'], spec['context_evidence_allowed'])
        assert not support(sufficient + ['b06:s99'], spec['evidence'], spec['context_evidence_allowed'])
    for insufficient in ([], ['b06:s02']):
        assert not support(insufficient, spec['evidence'], spec['context_evidence_allowed'])
