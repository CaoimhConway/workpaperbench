import copy
import importlib.util
import json
from pathlib import Path

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location('workpaperbench.alternative', ROOT / 'config/scorers/workflow-1.2.0.py')
SCORER = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(SCORER)


def read(path):
    return json.loads(path.read_text())


def test_new_catalog_only_changes_identity_and_three_evidence_options():
    for key in load(ROOT, 'workflow-v7')['tasks']:
        _, _, old = load(ROOT, 'workflow-v6', key)
        _, _, new = load(ROOT, 'workflow-v7', key)
        assert {p.relative_to(old) for p in old.rglob('*') if p.is_file()} == {
            p.relative_to(new) for p in new.rglob('*') if p.is_file()}
        for path in old.rglob('*'):
            if not path.is_file() or path.name in ('gold.json', 'authoring.json'):
                continue
            expected = path.read_bytes().replace(('workflow-v6-' + key).encode(),
                                                ('workflow-v7-' + key).encode())
            assert expected == (new / path.relative_to(old)).read_bytes()
        before, after = read(old / 'tests/gold.json'), read(new / 'tests/gold.json')
        expected = copy.deepcopy(before)
        expected['task_id'] = 'workflow-v7-' + key
        expected['hashes'] = after['hashes']
        if key == 'a01':
            for name in ('quarter_model', 'quarter_reconciliation'):
                expected['tables'][name]['evidence'].append(['a03:s05'])
            expected['claims']['claim_1']['evidence'].append(['a03:s05'])
        assert expected == after


def test_segment_totals_independently_reproduce_quarters_and_margin_change():
    task = ROOT / 'datasets/workflow-v7/tasks/a01'
    source = next(item for item in read(task / 'environment/evidence.json') if item['id'] == 'a03:s05')
    rows = json.loads(source['text'])
    totals = [[float(value.replace('$', '').replace(',', '')) for value in row[1:] if value]
              for row in rows if row[0] == 'Total']
    assert totals == [[69632, 62020, 135217, 118537], [31653, 27032, 62205, 53927]]
    revenue, income = totals
    quarters, reconciliation = [], []
    for year, current, half in [(2024, 1, 3), (2025, 0, 2)]:
        r1, o1 = revenue[half] - revenue[current], income[half] - income[current]
        quarters.extend([[year, 1, r1, o1, 100 * o1 / r1],
                         [year, 2, revenue[current], income[current], 100 * income[current] / revenue[current]]])
        reconciliation.append([year, 10000 * (income[current] / revenue[current] - o1 / r1)])
    gold = read(task / 'tests/gold.json')
    for name, actual in [('quarter_model', quarters), ('quarter_reconciliation', reconciliation)]:
        spec = gold['tables'][name]
        assert SCORER.compare({'columns': list(spec['columns']), 'rows': actual}, spec, spec['rows'])
    assert reconciliation[1][1] < 0
    assert gold['claims']['claim_1']['verdict'] == 'contradicted'


def test_alternative_and_original_citations_pass_but_incomplete_and_unrelated_fail():
    before = read(ROOT / 'datasets/workflow-v6/tasks/a01/tests/gold.json')
    after = read(ROOT / 'datasets/workflow-v7/tasks/a01/tests/gold.json')
    for group, names in [('tables', ['quarter_model', 'quarter_reconciliation']), ('claims', ['claim_1'])]:
        for name in names:
            old, new = before[group][name], after[group][name]
            assert not SCORER.supported(['a03:s05'], old['evidence'], old['context_evidence_allowed'])
            for evidence in [['a03:s02', 'a03:s03'], ['a03:s05'], ['a03:s05 - consolidated total rows']]:
                assert SCORER.supported(evidence, new['evidence'], new['context_evidence_allowed'])
            for evidence in [['a03:s02'], ['a03:s03'], ['a03:s06'], ['a03:s05', 'a03:s01'], ['a03:s05', 'a03:s99']]:
                assert not SCORER.supported(evidence, new['evidence'], new['context_evidence_allowed'])


def test_example_preserves_retained_sql_and_only_updates_catalog_identity():
    old, new = ROOT / 'examples/block-workpaper-v6', ROOT / 'examples/block-workpaper-v7'
    for path in old.iterdir():
        assert path.read_bytes().replace(b'workflow-v6-c01', b'workflow-v7-c01') == (new / path.name).read_bytes()
