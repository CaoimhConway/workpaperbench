import json
from pathlib import Path

from workpaperbench.catalog import load
from workpaperbench.workflow_grading import supported

ROOT = Path(__file__).resolve().parents[1]


def test_every_reference_has_sufficient_known_source_support():
    manifest = load(ROOT, 'workflow-v4')
    for key in manifest['tasks']:
        _, _, task = load(ROOT, 'workflow-v4', key)
        gold = json.loads((task / 'tests/gold.json').read_text())
        reference = json.loads((task / 'tests/reference.json').read_text())
        available = {entry['id'] for entry in json.loads((task / 'environment/evidence.json').read_text())}
        assert set(gold['context_evidence_allowed']) == available
        for role in ('tables', 'claims'):
            for entry in reference[role]:
                options = gold[role][entry['id']]['evidence']
                assert all(set(option) <= available for option in options)
                assert supported(entry['evidence'], options, available)
                assert supported(list(available), options, available)
                assert not supported([], options, available)
                assert not supported(entry['evidence'] + ['invented:source'], options, available)


def test_sbc_support_covers_both_actual_reports_and_dates():
    _, _, task = load(ROOT, 'workflow-v4', 'b01')
    gold = json.loads((task / 'tests/gold.json').read_text())
    entries = {entry['id']: entry for entry in json.loads((task / 'environment/evidence.json').read_text())}
    coverage = gold['tables']['reserve_coverage']['evidence']
    assert coverage == [['b01:s01', 'b01:s04']]
    assert 'May report table' in entries['b01:s01']['text']
    assert 'June report table' in entries['b01:s04']['text']
    assert not supported(['b01:s01', 'b01:s02'], coverage, gold['context_evidence_allowed'])
    dates = gold['tables']['signature_lag']['evidence']
    assert dates[0] == ['b01:s03', 'b01:s06']
    assert entries['b01:s01']['report_signed_date'] == entries['b01:s03']['report_signed_date']
    assert entries['b01:s04']['report_signed_date'] == entries['b01:s06']['report_signed_date']
    for option in dates:
        assert {entries[identifier]['period'].split()[0] for identifier in option} == {'2025-05-31', '2025-06-30'}


def test_evidence_correction_preserves_all_financial_rules():
    manifest = load(ROOT, 'workflow-v4')
    for key in manifest['tasks']:
        _, _, old = load(ROOT, 'workflow-v3', key)
        _, _, new = load(ROOT, 'workflow-v4', key)
        old_gold = json.loads((old / 'tests/gold.json').read_text())
        new_gold = json.loads((new / 'tests/gold.json').read_text())
        for gold in (old_gold, new_gold):
            for name in ('task_id', 'hashes', 'context_evidence_allowed'):
                gold.pop(name, None)
            for role in ('tables', 'claims'):
                for value in gold[role].values():
                    value.pop('evidence')
        assert old_gold == new_gold
        for path in old.rglob('*.sqlite'):
            assert path.read_bytes() == (new / path.relative_to(old)).read_bytes()
        for path in (old / 'solution').glob('*.sql'):
            assert path.read_bytes() == (new / 'solution' / path.name).read_bytes()
        assert (old / 'environment/evidence.json').read_bytes() == (new / 'environment/evidence.json').read_bytes()
        assert (old / 'environment/sources.md').read_bytes() == (new / 'environment/sources.md').read_bytes()
