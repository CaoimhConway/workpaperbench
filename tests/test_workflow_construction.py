import copy
from datetime import date
import importlib.util
import json
from pathlib import Path
import re

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location('workpaperbench.construction', ROOT / 'config/scorers/workflow-1.2.0.py')
SCORER = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(SCORER)


def read(path):
    return json.loads(path.read_text())


def test_construction_is_versioned_and_keeps_financial_targets_sources_and_controls():
    prior, current = load(ROOT, 'workflow-v7'), load(ROOT, 'workflow-v8')
    assert current['evaluation_track'] == 'construction'
    assert current['prior_catalog'] == prior['manifest_id']
    assert current['scorer_sha256'] == prior['scorer_sha256']
    assert set(current['tasks']) == set(prior['tasks'])
    for key in current['tasks']:
        _, before_spec, old = load(ROOT, 'workflow-v7', key)
        _, after_spec, new = load(ROOT, 'workflow-v8', key)
        assert after_spec['evaluation_track'] == 'construction'
        assert before_spec['split'] == after_spec['split']
        assert before_spec['source_group'] == after_spec['source_group']
        before, after = read(old / 'tests/gold.json'), read(new / 'tests/gold.json')
        expected = copy.deepcopy(before)
        expected['task_id'] = 'workflow-v8-' + key
        expected['hashes'] = after['hashes']
        if key == 'b01':
            date_pairs = [[f'b01:s0{may}', f'b01:s0{june}']
                          for may in (1, 2, 3) for june in (4, 5, 6)]
            expected['tables']['signature_lag']['evidence'] = date_pairs
            expected['claims']['claim_2']['evidence'] = date_pairs
        assert expected == after
        changed = {'instruction.md', 'authoring.json', 'environment/Dockerfile', 'tests/gold.json'}
        if key == 'b01':
            changed.add('environment/output_contract.json')
        old_files = {path.relative_to(old).as_posix() for path in old.rglob('*') if path.is_file()}
        removed = {'environment/starting_' + name + '.sql' for name in before['tables']}
        assert {path.relative_to(new).as_posix() for path in new.rglob('*') if path.is_file()} == old_files - removed
        for name in old_files - removed - changed:
            expected_bytes = (old / name).read_bytes().replace(('workflow-v7-' + key).encode(),
                                                             ('workflow-v8-' + key).encode())
            assert expected_bytes == (new / name).read_bytes()


def test_candidate_context_has_no_starters_or_answers_and_prompts_request_construction():
    for key in load(ROOT, 'workflow-v8')['tasks']:
        _, _, task = load(ROOT, 'workflow-v8', key)
        environment = task / 'environment'
        assert {path.name for path in environment.iterdir()} == {
            'Dockerfile', 'data.sqlite', 'evidence.json', 'sources.md', 'schema.json', 'output_contract.json'}
        dockerfile = (environment / 'Dockerfile').read_text()
        assert [line for line in dockerfile.splitlines() if line.startswith('COPY ')] == [
            'COPY data.sqlite evidence.json sources.md schema.json output_contract.json /workspace/']
        instruction = (task / 'instruction.md').read_text()
        assert 'This construction track supplies no starting SQL.' in instruction
        assert not re.search(r'\b(repair|starting|existing|valid SQL)\b', instruction.split('\n\n')[1], re.I)
        assert 'starting_' not in (environment / 'output_contract.json').read_text()
        assert read(task / 'authoring.json')['evaluation_track'] == 'construction'


def test_only_two_brale_assertions_change_and_source_values_entail_their_verdicts():
    old = ROOT / 'datasets/workflow-v7/tasks/b01'
    new = ROOT / 'datasets/workflow-v8/tasks/b01'
    before, after = read(old / 'environment/output_contract.json'), read(new / 'environment/output_contract.json')
    expected = copy.deepcopy(before)
    expected['claim_assertions'].update({
        'claim_2': 'The June report was signed more calendar days after its economic observation than the May report.',
        'claim_3': 'At least one observation date shows reserve assets greater than issued SBC units at USD 1 per token.'})
    assert expected == after
    observations = json.loads((new / 'environment/sources.md').read_text().split('reserve_reports\n', 1)[1])
    assert [row['report_date'] for row in observations] == ['2025-05-31', '2025-06-30']
    days = [(date.fromisoformat(row['report_signed_date']) - date.fromisoformat(row['report_date'])).days
            for row in observations]
    assert days == [12, 16]
    assert days[1] > days[0]
    assert all(row['cash_equivalents_usd'] + row['us_government_debt_usd'] == row['reported_reserve_fv_usd'] == row['issued_sbc']
               for row in observations)
    gold = read(new / 'tests/gold.json')
    assert gold['claims']['claim_2']['verdict'] == 'supported'
    assert gold['claims']['claim_3']['verdict'] == 'contradicted'
    coverage = gold['claims']['claim_3']
    assert not any(row['reported_reserve_fv_usd'] > row['issued_sbc'] for row in observations)
    assert SCORER.supported(['b01:s01', 'b01:s04'], coverage['evidence'], coverage['context_evidence_allowed'])
    for index, source_id in enumerate(('b01:s01', 'b01:s04')):
        assert not SCORER.supported([source_id], coverage['evidence'], coverage['context_evidence_allowed'])
        # Either singleton leaves the other date free to support the existential.
        possible = copy.deepcopy(observations)
        other = possible[1 - index]
        other['reported_reserve_fv_usd'] += 1
        other['cash_equivalents_usd'] += 1
        assert possible[index] == observations[index]
        assert any(row['reported_reserve_fv_usd'] > row['issued_sbc'] for row in possible)
    for name in ('claim_2', 'claim_3'):
        spec = gold['claims'][name]
        for option in spec['evidence']:
            assert SCORER.supported(option, spec['evidence'], spec['context_evidence_allowed'])
            assert not SCORER.supported(option + ['b01:s99'], spec['evidence'], spec['context_evidence_allowed'])
        assert not SCORER.supported(['b01:s03'], spec['evidence'], spec['context_evidence_allowed'])


def test_every_brale_metadata_pair_supports_dates_but_one_month_cannot():
    task = ROOT / 'datasets/workflow-v8/tasks/b01'
    evidence = read(task / 'environment/evidence.json')
    by_month = {'2025-05-31': [], '2025-06-30': []}
    for item in evidence:
        observed = item['period'][:10]
        lag = (date.fromisoformat(item['report_signed_date']) - date.fromisoformat(observed)).days
        assert lag == {'2025-05-31': 12, '2025-06-30': 16}[observed]
        by_month[observed].append(item['id'])
    assert {month: len(ids) for month, ids in by_month.items()} == {'2025-05-31': 3, '2025-06-30': 3}
    expected_pairs = {tuple([may, june]) for may in by_month['2025-05-31'] for june in by_month['2025-06-30']}
    gold = read(task / 'tests/gold.json')
    for spec in (gold['tables']['signature_lag'], gold['claims']['claim_2']):
        assert {tuple(pair) for pair in spec['evidence']} == expected_pairs
        for pair in expected_pairs:
            assert SCORER.supported(pair, spec['evidence'], spec['context_evidence_allowed'])
        for incomplete in [*by_month.values(), *[[item['id']] for item in evidence]]:
            assert not SCORER.supported(incomplete, spec['evidence'], spec['context_evidence_allowed'])
        assert not SCORER.supported(['b01:s01', 'b01:s04', 'b01:s99'], spec['evidence'], spec['context_evidence_allowed'])


def test_example_keeps_identical_sql_and_only_changes_catalog_identity():
    old, new = ROOT / 'examples/block-workpaper-v7', ROOT / 'examples/block-workpaper-v8'
    for path in old.iterdir():
        assert path.read_bytes().replace(b'workflow-v7-c01', b'workflow-v8-c01') == (new / path.name).read_bytes()
