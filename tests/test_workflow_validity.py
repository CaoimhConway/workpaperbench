import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location('workpaperbench.validity', ROOT / 'config/scorers/workflow-1.2.0.py')
SCORER = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(SCORER)


def read(path):
    return json.loads(path.read_text())


def test_revision_preserves_every_source_sql_and_financial_target():
    for key in load(ROOT, 'workflow-v6')['tasks']:
        _, _, old = load(ROOT, 'workflow-v5', key)
        _, _, new = load(ROOT, 'workflow-v6', key)
        for folder in ('environment', 'solution', 'tests'):
            for path in (old / folder).iterdir():
                if path.suffix in ('.sqlite', '.sql') or path.name in ('sources.md', 'evidence.json'):
                    assert path.read_bytes() == (new / folder / path.name).read_bytes()
        before, after = read(old / 'tests/gold.json'), read(new / 'tests/gold.json')
        assert before['controls'] == after['controls']
        for name, spec in before['tables'].items():
            assert spec['rows'] == after['tables'][name]['rows']
            assert spec['evidence'] == after['tables'][name]['evidence']
            for column, definition in spec['columns'].items():
                assert definition.items() <= after['tables'][name]['columns'][column].items()


def test_claims_have_no_universal_abstention_slot_and_only_one_valid_label():
    totals, unresolved_per_case, positions, dev = Counter(), Counter(), set(), Counter()
    review = read(ROOT / 'config/workflow-claim-review.json')
    for key, spec in load(ROOT, 'workflow-v6')['tasks'].items():
        _, _, task = load(ROOT, 'workflow-v6', key)
        gold = read(task / 'tests/gold.json')
        contract = read(task / 'environment/output_contract.json')
        reference = read(task / 'tests/reference.json')
        assert list(gold['claims']) == list(contract['claim_assertions']) == ['claim_1', 'claim_2', 'claim_3']
        labels = [item['verdict'] for item in gold['claims'].values()]
        totals.update(labels)
        unresolved_per_case[labels.count('unresolved')] += 1
        for name, item in gold['claims'].items():
            assert 'accepted_verdicts' not in item
            assert sum(SCORER.verdict_correct({'verdict': label}, item)
                       for label in ('supported', 'contradicted', 'unresolved')) == 1
            if item['verdict'] == 'unresolved':
                positions.add(name)
        if spec['split'] == 'development':
            dev[review['claims'][key]['verdict']] += 1
        for claim in reference['claims']:
            expected = gold['claims'][claim['id']]
            assert SCORER.verdict_correct(claim, expected)
            assert SCORER.supported(claim['evidence'], expected['evidence'], expected['context_evidence_allowed'])
    assert totals == {'supported': 37, 'contradicted': 43, 'unresolved': 10}
    assert unresolved_per_case == {0: 20, 1: 10}
    assert positions == {'claim_1', 'claim_2', 'claim_3'}
    assert dev == {'supported': 2, 'contradicted': 2, 'unresolved': 2}


def test_new_evidence_accepts_all_reviewed_paths_and_rejects_unrelated_sections():
    for key in load(ROOT, 'workflow-v6')['tasks']:
        _, _, task = load(ROOT, 'workflow-v6', key)
        gold = read(task / 'tests/gold.json')
        known = {entry['id'] for entry in read(task / 'environment/evidence.json')}
        rejects_dump = False
        for spec in [*gold['tables'].values(), *gold['claims'].values()]:
            options, context = spec['evidence'], spec['context_evidence_allowed']
            allowed = set(context).union(*map(set, options))
            assert allowed <= known
            for option in options:
                assert SCORER.supported([' and '.join(option + context) + ' - FY2025:Q2 explanation'], options, context)
                for unrelated in known - allowed:
                    assert not SCORER.supported(option + [unrelated], options, context)
            rejects_dump |= not SCORER.supported(known, options, context)
        assert rejects_dump


def test_corrected_replay_keeps_substantive_model_failures_and_original_bytes():
    report = read(ROOT / 'reports/workflow-v5/corrected-replay.json')
    assert report['inference'] is False
    assert report['scorer_sha256'] == hashlib.sha256((ROOT / 'config/scorers/workflow-1.2.0.py').read_bytes()).hexdigest()
    results = {entry['task']: entry for entry in report['attempts']}
    assert results['c01']['verdict']['complete'] is True
    microsoft = results['a01']['verdict']
    assert microsoft['checks']['evidence'] is True
    assert microsoft['checks']['claim_verdicts'] is True
    assert microsoft['details']['tables']['quarter_reconciliation']['original_error'] == 'numeric'
    brale = results['b01']['verdict']
    assert brale['checks']['numerical_tables'] is True
    assert brale['details']['tables']['reserve_coverage']['controls']['identical_export_duplicate'] is False
    for entry in results.values():
        directory = ROOT / 'reports/workflow-v5/submissions' / entry['attempt_id']
        assert read(directory / 'receipt.json')['verdict'] == entry['original_verdict']
        for name, checksum in entry['files_sha256'].items():
            assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == checksum
