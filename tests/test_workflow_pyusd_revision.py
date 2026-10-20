import copy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location('workpaperbench.pyusd', ROOT / 'config/scorers/workflow-1.2.0.py')
SCORER = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(SCORER)


def read(path):
    return json.loads(path.read_text())


def test_revision_preserves_all_financial_inputs_targets_and_controls():
    prior, current = load(ROOT, 'workflow-v8'), load(ROOT, 'workflow-v9')
    assert current['prior_catalog'] == prior['manifest_id']
    assert current['scorer_sha256'] == prior['scorer_sha256']
    for key in current['tasks']:
        _, _, old = load(ROOT, 'workflow-v8', key)
        _, _, new = load(ROOT, 'workflow-v9', key)
        assert {p.relative_to(old) for p in old.rglob('*') if p.is_file()} == {
            p.relative_to(new) for p in new.rglob('*') if p.is_file()}
        for path in old.rglob('*'):
            if not path.is_file() or path.name in ('gold.json', 'authoring.json'):
                continue
            if key == 'b02' and path.name == 'output_contract.json':
                expected = read(path)
                actual = read(new / path.relative_to(old))
                expected['definitions']['treasury_valuation'] += ' ' + current['pyusd_revision']['treasury_residual_definition']
                assert actual == expected
            else:
                expected = path.read_bytes().replace(('workflow-v8-' + key).encode(),
                                                    ('workflow-v9-' + key).encode())
                assert expected == (new / path.relative_to(old)).read_bytes()
        expected = copy.deepcopy(read(old / 'tests/gold.json'))
        after = read(new / 'tests/gold.json')
        expected['task_id'] = 'workflow-v9-' + key
        expected['hashes'] = after['hashes']
        if key == 'b02':
            expected['claims']['claim_3']['evidence'].append(['b02:s01', 'b02:s02'])
        assert expected == after


def test_both_reports_support_all_observation_date_comparisons():
    task = ROOT / 'datasets/workflow-v9/tasks/b02'
    sources = {row['id']: row for row in read(task / 'environment/evidence.json')}
    assert '3,608,697,613' in sources['b02:s01']['text']
    assert '3,622,145,209' in sources['b02:s01']['text']
    assert all(date in sources['b02:s02']['text'] for date in ('February 10', 'February 27'))
    gold = read(task / 'tests/gold.json')
    table = gold['tables']['qualified_coverage']
    columns = list(table['columns'])
    rows = [dict(zip(columns, row)) for row in table['rows']]
    surpluses = [Decimal(str(row['assets_usd'])) - Decimal(str(row['redeemable_tokens'])) for row in rows]
    assert surpluses == list(map(Decimal, ('13447596', '17318105', '12745159')))
    assert gold['claims']['claim_3']['verdict'] == 'supported'


def test_sufficient_alternative_passes_but_incomplete_and_unknown_citations_fail():
    task = ROOT / 'datasets/workflow-v9/tasks/b02'
    gold = read(task / 'tests/gold.json')
    spec = gold['claims']['claim_3']
    for evidence in (['b02:s01', 'b02:s02'], ['b02:s01', 'b02:s02', 'b02:s05']):
        assert SCORER.supported(evidence, spec['evidence'], spec['context_evidence_allowed'])
    for evidence in ([], ['b02:s01'], ['b02:s02'], ['b02:s05'], ['b02:s01', 'b02:s02', 'b02:s99']):
        assert not SCORER.supported(evidence, spec['evidence'], spec['context_evidence_allowed'])
    for name in ('qualified_coverage', 'treasury_valuation'):
        spec = gold['tables'][name]
        assert not SCORER.supported(['b02:s01', 'b02:s02'], spec['evidence'], spec['context_evidence_allowed'])


def test_residual_direction_matches_independent_discrepancy_target():
    task = ROOT / 'datasets/workflow-v9/tasks/b02'
    contract, gold = read(task / 'environment/output_contract.json'), read(task / 'tests/gold.json')
    assert 'deduplicated Treasury-holding fair value less the reported Treasury asset-category fair value' in contract['definitions']['treasury_valuation']
    control = next(row for row in gold['controls'] if row['name'] == 'independent_disclosure_discrepancy')
    assert control['changes'] == [['treasury_holdings', 0, 'fair_value_usd', 17]]
    columns = list(gold['tables']['treasury_valuation']['columns'])
    original = dict(zip(columns, gold['tables']['treasury_valuation']['rows'][0]))
    changed = dict(zip(columns, control['tables']['treasury_valuation'][0]))
    assert changed['fair_value_usd'] - original['fair_value_usd'] == 17
    assert changed['residual_usd'] == 17
