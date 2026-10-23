import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_workflow_evidence_revision import construct

MODULE = importlib.util.spec_from_file_location(
    'workpaperbench.workflow_evidence_revision_scorer', ROOT / 'config/scorers/workflow-1.2.1.py')
SCORER = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(SCORER)


def read(path):
    return json.loads(path.read_text())


def mapping(dataset, key, group, name):
    return read(ROOT / 'datasets' / dataset / 'tasks' / key / 'tests/gold.json')[group][name]


def accepts(key, group, name, citations):
    spec = mapping('workflow-v14', key, group, name)
    return SCORER.supported(citations, spec['evidence'], spec['context_evidence_allowed'])


def test_review_covers_every_output_and_binds_original_mappings():
    review = read(ROOT / 'config/workflow-evidence-review.json')
    prior = load(ROOT, 'workflow-v13')
    assert review['base_manifest_id'] == prior['manifest_id']
    expected = set()
    for key in prior['tasks']:
        gold = read(ROOT / 'datasets/workflow-v13/tasks' / key / 'tests/gold.json')
        for group in ('tables', 'claims'):
            for name, spec in gold[group].items():
                expected.add((key, group, name))
    actual = {(r['task'], r['group'], r['output']) for r in review['mappings']}
    assert len(review['mappings']) == len(actual) == 180
    assert actual == expected
    for row in review['mappings']:
        old = mapping('workflow-v13', row['task'], row['group'], row['output'])
        assert row['original_mapping'] == {
            key: old[key] for key in ('evidence', 'context_evidence_allowed')}
        for field in ('result_or_proposition', 'entity', 'period', 'unit', 'accounting_scope',
                      'source_references', 'sufficient_source_combinations',
                      'insufficient_or_missing_essential_examples', 'source_based_rationale'):
            assert row[field], (row['task'], row['output'], field)


def test_revision_changes_only_grading_and_identity_metadata():
    prior, current = load(ROOT, 'workflow-v13'), load(ROOT, 'workflow-v14')
    review = read(ROOT / 'config/workflow-evidence-review.json')
    assert current['prior_catalog'] == prior['manifest_id']
    for field in ('scorer_version', 'scorer_sha256', 'sql_worker_sha256'):
        assert current[field] == prior[field]
    assert current['evidence_revision']['model_visible_changes_except_identity'] is False
    decisions = {(r['task'], r['group'], r['output']): r for r in review['mappings']}
    for key in prior['tasks']:
        _, before, old = load(ROOT, 'workflow-v13', key)
        _, after, new = load(ROOT, 'workflow-v14', key)
        original = read(old / 'tests/gold.json')
        expected = copy.deepcopy(original)
        actual = read(new / 'tests/gold.json')
        expected.update(task_id=after['task_id'], hashes=actual['hashes'])
        for group in ('tables', 'claims'):
            for name, spec in expected[group].items():
                spec.update(decisions[key, group, name]['corrected_mapping'])
        assert actual == expected
        assert (before['split'], before['source_group']) == (after['split'], after['source_group'])
        reference_updates = review.get('authored_reference_updates', {}).get(key, {})
        original_reference = (old / 'tests/reference.json').read_text().replace(
            before['task_id'], after['task_id'])
        reference = json.loads(original_reference)
        for group, outputs in reference_updates.items():
            for name, citations in outputs.items():
                next(r for r in reference[group] if r['id'] == name)['evidence'] = citations
        assert reference == read(new / 'tests/reference.json')
        for path in old.rglob('*'):
            if not path.is_file():
                continue
            relative = path.relative_to(old)
            if str(relative) in ('tests/gold.json', 'tests/reference.json', 'authoring.json'):
                continue
            expected_bytes = path.read_bytes().replace(before['task_id'].encode(), after['task_id'].encode())
            if str(relative) == 'solution/solve.sh' and reference_updates:
                expected_bytes = expected_bytes.replace(original_reference.strip().encode(),
                    (new / 'tests/reference.json').read_bytes().strip())
            assert expected_bytes == (new / relative).read_bytes(), (key, str(relative))
        assert {p.relative_to(old) for p in old.rglob('*') if p.is_file()} == {
            p.relative_to(new) for p in new.rglob('*') if p.is_file()}


def test_builder_reconstructs_exact_versioned_package(tmp_path):
    result = construct(tmp_path)
    assert result == read(ROOT / 'datasets/workflow-v14/manifest.json')
    for path in tmp_path.rglob('*'):
        if path.is_file():
            assert path.read_bytes() == (ROOT / 'datasets/workflow-v14' / path.relative_to(tmp_path)).read_bytes()


@pytest.mark.parametrize('key,group,name,citations,expected', [
    ('a04', 'claims', 'claim_2', ['a04:s01', 'a04:s02', 'a04:s03'], True),
    ('a04', 'claims', 'claim_2', ['a04:s01', 'a04:s02'], True),
    ('a04', 'claims', 'claim_2', ['a04:s01', 'a04:s03'], False),
    ('a04', 'claims', 'claim_2', ['a04:s02', 'a04:s03'], False),
    ('a04', 'claims', 'claim_2', ['a04:s03'], False),
    ('a04', 'claims', 'claim_2', ['a04:s01', 'a04:s02', 'a04:s99'], False),
    ('a10', 'tables', 'revenue_growth_bridge', ['a10:s01'], True),
    ('a10', 'tables', 'revenue_growth_bridge', ['a10:s01', 'a10:s03'], True),
    ('a10', 'tables', 'revenue_growth_bridge', ['a10:s01', 'a10:s02'], True),
    ('a10', 'tables', 'revenue_growth_bridge', ['a10:s03'], False),
    ('a10', 'tables', 'revenue_growth_bridge', ['a10:s02'], False),
    ('a03', 'claims', 'claim_2', ['a03:s02', 'a03:s03'], True),
    ('a03', 'claims', 'claim_2', ['a03:s03'], False),
    ('a03', 'claims', 'claim_2', ['a03:s02'], False),
    ('a09', 'claims', 'claim_1', ['a09:s02', 'a09:s03'], True),
    ('a09', 'claims', 'claim_1', ['a09:s03'], False),
    ('a09', 'claims', 'claim_1', ['a09:s02'], False),
    ('a01', 'tables', 'quarter_model', ['a03:s02', 'a03:s03'], True),
    ('a01', 'tables', 'quarter_model', ['a03:s05'], True),
    ('a01', 'tables', 'quarter_model', ['a03:s02'], False),
    ('a02', 'claims', 'claim_1', ['a02:s03', 'a02:s02'], False),
    ('b07', 'tables', 'quarter_cash', ['b07:s01'], True),
    ('b07', 'tables', 'quarter_cash', ['b07:s01', 'b07:s02', 'b07:s03'], True),
    ('b07', 'tables', 'quarter_cash', ['b07:s02', 'b07:s03'], False),
    ('b04', 'claims', 'claim_1', ['b04:s03', 'b04:s02'], False),
    ('b07', 'claims', 'claim_1', ['b07:s02', 'b07:s03'], False),
    ('b10', 'claims', 'claim_1', ['b10:s03', 'b10:s01'], False),
    ('c04', 'claims', 'claim_3', ['c04:s01'], True),
    ('c04', 'claims', 'claim_3', ['c04:s02'], False),
])
def test_source_grounded_positive_and_negative_citations(key, group, name, citations, expected):
    assert accepts(key, group, name, citations) is expected


def test_period_context_does_not_replace_cash_observations_or_issuer_definition():
    sources = (ROOT / 'datasets/workflow-v13/tasks/a04/environment/sources.md').read_text()
    assert 'Q4 amounts cover three months, annual amounts cover twelve' in sources
    assert 'net of sales proceeds and incentives' in sources
    assert 'does not subtract finance-lease principal' in sources
    assert (115877 - (82999 - 5341)) > (139514 - (131819 - 3499))


def test_reported_growth_uses_statement_totals_and_not_fx_adjusted_prior():
    task = ROOT / 'datasets/workflow-v13/tasks/a10'
    sources = (task / 'environment/sources.md').read_text()
    observations, _ = json.JSONDecoder().raw_decode(sources.split('Source-derived observations\n\n', 1)[1])
    rows = {r['period']: r for r in observations['income']}
    assert rows['FY2025']['revenue_usd_million'] - rows['FY2024']['revenue_usd_million'] == 6280
    assert rows['Q4FY2025']['revenue_usd_million'] - rows['Q4FY2024']['revenue_usd_million'] == 1801
    for row in rows.values():
        assert sum(row[n + '_usd_million'] for n in ('discount', 'card_fees', 'service_other', 'net_interest')) == row['revenue_usd_million']
    assert 'Prior FX-adjusted revenue is USD 17,349 million and USD 66,083 million' in sources


def test_review_fixtures_cover_each_corrected_mapping():
    review = read(ROOT / 'config/workflow-evidence-review.json')
    for row in review['mappings']:
        if not row['changed']:
            continue
        for case in row['regression_cases']:
            assert accepts(row['task'], row['group'], row['output'], case['citations']) is case['expected']
        assert any(case['expected'] for case in row['regression_cases'])
        assert any(not case['expected'] for case in row['regression_cases'])
