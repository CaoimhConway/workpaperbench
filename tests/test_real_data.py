"""Source and control invariants for the separate real-v1 suite."""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from workpaperbench.grading import grade

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / 'datasets/real-v1'


def evaluate(tmp_path, task, mutate=None):
    trusted = DATASET / 'tasks' / task / 'tests'
    answer = json.loads((trusted / 'reference.json').read_text())
    if mutate:
        mutate(answer)
    output = tmp_path / 'answer.json'
    output.write_text(json.dumps(answer))
    return grade(tmp_path, trusted)


@pytest.mark.parametrize('task', [f'wp0{i}' for i in range(1, 9)])
def test_new_references_and_valid_sql_alternatives(tmp_path, task):
    assert evaluate(tmp_path, task)['complete'] is True
    def wrapper(answer):
        for claim in answer['answers']:
            if claim['sql']:
                claim['sql'] = 'SELECT value FROM (' + claim['sql'] + ')'
    assert evaluate(tmp_path, task, wrapper)['complete'] is True


def test_same_amount_distinct_events_is_rejected(tmp_path):
    def wrong(answer):
        answer['answers'][0]['sql'] = "SELECT SUM(DISTINCT amount_units) AS value FROM events WHERE event_kind='transfer'"
    result = evaluate(tmp_path, 'wp02', wrong)
    assert result['checks']['numerical'] is True
    assert result['checks']['replay'] is False
    assert result['complete'] is False


@pytest.mark.parametrize('sql', [
    "SELECT SUM(amount_units) AS value FROM (SELECT DISTINCT event_id, amount_units FROM events WHERE event_kind='transfer')",
    "SELECT SUM(amount_units) AS value FROM (SELECT event_id,MIN(amount_units) amount_units FROM events WHERE event_kind='transfer' GROUP BY event_id)",
    "WITH e AS (SELECT amount_units,ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY export_row) n FROM events WHERE event_kind='transfer') SELECT SUM(amount_units) AS value FROM e WHERE n=1",
])
def test_event_identity_equivalents_are_accepted(tmp_path, sql):
    def valid(answer):
        answer['answers'][0]['sql'] = sql
    assert evaluate(tmp_path, 'wp02', valid)['complete'] is True


def test_event_totals_independent_of_reference_query():
    source = json.loads((DATASET / 'sources/wp02.json').read_text())
    for key, expected in (('tables', 1000), ('changed_tables', 1220)):
        events = {}
        for _, event_id, _, kind, amount in source[key]['events']['rows']:
            if kind == 'transfer':
                if event_id in events:
                    assert events[event_id] == amount
                events[event_id] = amount
        assert sum(events.values()) == expected
        assert len(set(events.values())) < len(events)


def test_filing_references_independently_recalculated():
    tesla = json.loads((DATASET / 'sources/wp01.json').read_text())
    q1 = Decimal(2225) - Decimal(1074)
    assert float(q1) == tesla['gold']['answers']['q1_rd']['value']
    assert abs(float((Decimal(1074) - q1) / q1 * 100) - tesla['gold']['answers']['sequential_change']['value']) < 1e-9
    apple = json.loads((DATASET / 'sources/wp07.json').read_text())
    revenue = Decimal(46984) - Decimal(23867)
    profit = Decimal(34646) - Decimal(17809)
    margin = profit / revenue * 100
    change = Decimal(17809) / Decimal(23867) * 100 - margin
    assert float(revenue) == apple['gold']['answers']['q1_revenue']['value']
    assert abs(float(margin) - apple['gold']['answers']['q1_margin']['value']) < 1e-9
    assert abs(float(change) - apple['gold']['answers']['margin_change']['value']) < 1e-9


def test_original_dataset_remains_frozen():
    freeze = json.loads((ROOT / 'config/freeze.json').read_text())
    for name, digest in freeze['hashes'].items():
        if name.startswith('sources/') or (name.startswith('tasks/') and '/workpaperbench/' not in name) or name.startswith('config/'):
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest


def test_offline_reconstruction_preserves_frozen_package_bytes():
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_real_tasks.py'), '--check'], check=True, cwd=ROOT)


def test_reconstruction_compares_rows_and_duplicates_across_page_layouts(tmp_path):
    import sqlite3
    sys.path.insert(0, str(ROOT / 'scripts'))
    import build_real_tasks
    paths = [tmp_path / 'small.sqlite', tmp_path / 'large.sqlite']
    for path, page_size in zip(paths, (4096, 8192)):
        with sqlite3.connect(path) as db:
            db.execute(f'PRAGMA page_size={page_size}')
            db.execute('CREATE TABLE events(event_id TEXT,amount INTEGER)')
            db.executemany('INSERT INTO events VALUES (?,?)', [('e1', 100), ('e1', 100), ('e2', 100)])
    assert paths[0].read_bytes() != paths[1].read_bytes()
    assert build_real_tasks.sqlite_contents(paths[0]) == build_real_tasks.sqlite_contents(paths[1])
    with sqlite3.connect(paths[1]) as db:
        db.execute('DELETE FROM events WHERE rowid=1')
    assert build_real_tasks.sqlite_contents(paths[0]) != build_real_tasks.sqlite_contents(paths[1])


def test_new_contract_is_per_claim_before_evaluation():
    for instruction in (DATASET / 'tasks').glob('*/instruction.md'):
        assert 'evidence contract is per claim' in instruction.read_text()
        assert 'explicitly synthetic' in instruction.read_text()


def test_bitcoin_source_calculations_from_original_bytes():
    directory = DATASET / 'captures/bitcoin-halving'
    pages = {h: json.loads((directory / f'transactions-first25-{h}.response').read_bytes()) for h in (839999, 840000)}
    for height, page in pages.items():
        assert len(page) == 25
        assert len({t['txid'] for t in page}) == 25
        for tx in page[1:]:
            assert sum(i['prevout']['value'] for i in tx['vin']) - sum(o['value'] for o in tx['vout']) == tx['fee']
            assert tx['status']['block_height'] == height
    fees = sum(t['fee'] for t in pages[840000][1:])
    payout = sum(o['value'] for o in pages[840000][0]['vout'])
    assert fees == 2080158845 and payout - 312500000 == 3762561499
    gold = json.loads((DATASET / 'tasks/wp03/tests/gold.json').read_text())
    assert gold['answers']['sample_fees']['value'] == float(Decimal(fees) / 100000000)
    assert gold['answers']['claimed_above_subsidy']['value'] == float(Decimal(payout - 312500000) / 100000000)
    common = {t['version'] for t in pages[839999][1:]} & {t['version'] for t in pages[840000][1:]}
    assert common == {2}
    rates = {}
    for matched in (False, True):
        for height, page in pages.items():
            txs = [t for t in page[1:] if not matched or t['version'] in common]
            rates[matched, height] = Decimal(sum(t['fee'] for t in txs)) / sum((t['weight'] + 3) // 4 for t in txs)
    gold = json.loads((DATASET / 'tasks/wp06/tests/gold.json').read_text())
    for matched, name in ((False, 'sample_rate_change'), (True, 'matched_rate_change')):
        value = (rates[matched, 840000] / rates[matched, 839999] - 1) * 100
        assert abs(float(value) - gold['answers'][name]['value']) < 1e-8
    outputs = sum(o['value'] for t in pages[840000][1:] for o in t['vout'])
    assert outputs == 2757007836
    gold = json.loads((DATASET / 'tasks/wp08/tests/gold.json').read_text())
    assert gold['answers']['observed_outputs']['value'] == float(Decimal(outputs) / 100000000)


def test_circle_source_equation_and_units():
    source = json.loads((DATASET / 'captures/circle-usdc-jan2025.json').read_text())
    by_date = {r['report_date'][:10]: r for r in source['observations']}
    for r in by_date.values():
        assert r['total_supply_usdc'] - r['allowed_but_not_issued_usdc'] - r['access_denied_usdc'] == r['circulation_usdc_reported']
    p1 = Decimal(by_date['2025-01-06']['circulation_usdc_reported'])
    p2 = Decimal(by_date['2025-01-31']['circulation_usdc_reported'])
    gold = json.loads((DATASET / 'tasks/wp04/tests/gold.json').read_text())
    assert gold['answers']['circulating_end']['value'] == float(p2 / 1000000)
    assert abs(gold['answers']['circulating_growth']['value'] - float((p2 / p1 - 1) * 100)) < 1e-9
    assert gold['answers']['reserve_headroom']['value'] == 64.86063


def test_relevant_context_equivalence_is_not_hidden_citation_repetition(tmp_path):
    def context(answer):
        for claim in answer['answers']:
            claim['evidence'].append('chain:scope')
        answer['conclusion']['evidence'].append('chain:scope')
    assert evaluate(tmp_path, 'wp03', context)['complete'] is True


def test_contract_failure_does_not_change_correct_conclusion_verdict(tmp_path):
    def missing(answer):
        answer['conclusion']['evidence'] = ['chain:observations']
    verdict = evaluate(tmp_path, 'wp03', missing)
    assert verdict['complete'] is False
    assert verdict['details']['conclusion']['verdict'] is True
    assert verdict['details']['conclusion']['evidence'] is False
