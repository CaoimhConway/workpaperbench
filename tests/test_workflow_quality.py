import importlib.util
import itertools
import json
from pathlib import Path

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location('workpaperbench.reviewed_workflow', ROOT / 'config/scorers/workflow-1.1.0.py')
SCORER = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(SCORER)


def read(path):
    return json.loads(path.read_text())


def test_reviewed_support_accepts_alternatives_and_relevant_context():
    for key in load(ROOT, 'workflow-v5')['tasks']:
        _, _, task = load(ROOT, 'workflow-v5', key)
        gold, answer = read(task / 'tests/gold.json'), read(task / 'tests/reference.json')
        known = {entry['id'] for entry in read(task / 'environment/evidence.json')}
        rejects_dump = False
        for role in ('tables', 'claims'):
            for entry in answer[role]:
                spec = gold[role][entry['id']]
                options, context = spec['evidence'], spec['context_evidence_allowed']
                assert SCORER.supported(entry['evidence'], options, context)
                assert not SCORER.supported([], options, context)
                assert not SCORER.supported(entry['evidence'] + ['invented:source'], options, context)
                allowed = set(context).union(*map(set, options))
                assert allowed <= known
                for option in options:
                    for size in range(len(context) + 1):
                        for extras in itertools.combinations(context, size):
                            assert SCORER.supported(option + list(extras), options, context)
                    for unrelated in known - allowed:
                        assert not SCORER.supported(option + [unrelated], options, context)
                rejects_dump |= not SCORER.supported(known, options, context)
        assert rejects_dump, key


def test_original_sources_and_prior_controls_survive_quality_revision():
    review = read(ROOT / 'config/workflow-quality-review.json')
    for key in load(ROOT, 'workflow-v5')['tasks']:
        _, _, old = load(ROOT, 'workflow-v4', key)
        _, _, new = load(ROOT, 'workflow-v5', key)
        for name in ('evidence.json', 'sources.md', 'data.sqlite'):
            assert (old / 'environment' / name).read_bytes() == (new / 'environment' / name).read_bytes()
        for path in (old / 'tests').glob('*.sqlite'):
            assert path.read_bytes() == (new / 'tests' / path.name).read_bytes()
        removed = review['removed_identity_columns'].get(key, {})
        for folder, prefix in (('solution', ''), ('environment', 'starting_')):
            for path in (old / folder).glob(prefix + '*.sql'):
                table = path.stem.removeprefix(prefix)
                if table not in removed:
                    assert path.read_bytes() == (new / folder / path.name).read_bytes()
        old_gold, new_gold = read(old / 'tests/gold.json'), read(new / 'tests/gold.json')
        for name, spec in old_gold['tables'].items():
            keep = [i for i, column in enumerate(spec['columns']) if column not in removed.get(name, [])]
            assert new_gold['tables'][name]['rows'] == [[row[i] for i in keep] for row in spec['rows']]
            for before, after in zip(old_gold['controls'], new_gold['controls']):
                assert before['name'] == after['name']
                assert after['tables'][name] == [[row[i] for i in keep] for row in before['tables'][name]]


def test_discrepancy_controls_make_every_retained_zero_residual_informative():
    review = read(ROOT / 'config/workflow-quality-review.json')
    exercised = removed = 0
    for key, entry in review['residual_controls'].items():
        _, _, task = load(ROOT, 'workflow-v5', key)
        gold = read(task / 'tests/gold.json')
        for table, column in entry['remaining']:
            assert column not in gold['tables'][table]['columns']
            removed += 1
        if not entry['covered']:
            continue
        control = next(item for item in gold['controls'] if item['name'] == 'independent_disclosure_discrepancy')
        assert control['origin'] == 'authored_synthetic_counterfactual'
        for table, column in entry['covered']:
            spec = gold['tables'][table]
            index = list(spec['columns']).index(column)
            assert all(row[index] == 0 for row in spec['rows'])
            assert any(abs(row[index]) > spec['columns'][column]['tolerance'] for row in control['tables'][table])
            exercised += 1
    assert (exercised, removed) == (51, 3)
