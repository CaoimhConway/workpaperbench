"""Exact subset, settlement-value and threshold checks for the Veeco case."""
import copy
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from workflow_hard_convertibles import SQL, alternatives, calculate, controls, mistakes, specification


def inputs():
    source = json.loads((ROOT / 'datasets/workflow-hard-pilot-v2/sources/veeco-2024.json').read_text())
    data = {name: [dict(zip(table['columns'], row)) for row in table['rows']]
            for name, table in source['tables'].items()}
    return source, data


def execute(data, queries):
    source, _ = inputs()
    with sqlite3.connect(':memory:') as connection:
        for name, rows in data.items():
            columns = source['tables'][name]['columns']
            connection.execute('CREATE TABLE ' + name + ' (' + ','.join(k+' '+v for k,v in columns.items()) + ')')
            connection.executemany('INSERT INTO ' + name + ' VALUES (' + ','.join('?' for _ in columns) + ')',
                                   [tuple(row[k] for k in columns) for row in rows])
        return {name: [list(row) for row in connection.execute(query)] for name, query in queries.items()}


def equal(actual, expected):
    assert actual.keys() == expected.keys()
    for name in expected:
        assert len(actual[name]) == len(expected[name])
        for received, target in zip(sorted(actual[name]), sorted(expected[name])):
            for a, e in zip(received, target):
                if isinstance(e, str):
                    assert a == e
                else:
                    assert a == pytest.approx(e, rel=0, abs=1e-9)


def fraction(value):
    return Fraction(str(value))


def independent_subsets(data, price, income):
    """Exhaust all issuer-specific EPS cases with exact rational arithmetic."""
    terms = {r['note']: r for r in data['contract_terms']}
    basis = data['eps_basis'][0]
    candidates = []
    for enabled in itertools.product([False, True], repeat=3):
        numerator = fraction(income)
        denominator = fraction(basis['basic_shares']) + fraction(basis['award_shares'])
        included = []
        for row, include in zip(data['notes'], enabled):
            if not include:
                continue
            note = row['note']
            included.append(note)
            face = fraction(row['principal'])
            converted = face * fraction(terms[note]['conversion_rate']) / 1000
            if terms[note]['principal_settlement'] == 'cash':
                denominator += max(Fraction(0), (converted * fraction(price) - face) / fraction(price))
            else:
                denominator += converted
                numerator += fraction(row['coupon']) + fraction(row['amortization'])
        candidates.append((numerator / denominator, tuple(included)))
    return candidates


def independent_gross(data, price):
    """Value conservation between the rational holder payoff, cash and shares."""
    terms = {r['note']: r for r in data['contract_terms']}
    result = Fraction(0)
    for note in data['notes']:
        face = fraction(note['principal'])
        value = face * fraction(terms[note['note']]['conversion_rate']) * price / 1000
        payoff = max(face, value)
        cash = face if terms[note['note']]['principal_settlement'] == 'cash' or value <= face else 0
        result += (payoff - cash) / price
    return result


def test_source_identity_and_authentic_accounting_cross_check():
    source, data = inputs()
    expected = source.pop('extract_sha256')
    assert hashlib.sha256(json.dumps(source, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest() == expected
    assert len(source['captures']) == 2
    assert all(len(row['sha256']) == 64 and row['redistributed'] is False for row in source['captures'])
    assert {r['id'] for r in source['evidence']} == {'b01:s0'+str(n) for n in range(1, 9)}
    assert {r['note']: r['conversion_rate'] for r in data['contract_terms']}['2029'] == 34.2185
    assert {r['note']: r['conversion_rate'] for r in data['reported_rates']}['2029'] == 34.21852
    # The issuer's actual addback independently identifies the two cash-or-share
    # notes' total expense, including amortization and excluding the 2029 series.
    optional_expense = sum(fraction(r['coupon']) + fraction(r['amortization'])
                           for r in data['notes'] if r['note'] in ['2025', '2027'])
    assert optional_expense == fraction(data['eps_basis'][0]['reported_note_addback']) == Fraction(2054, 1000)
    assert sum(fraction(r['principal']) for r in data['notes']) == Fraction(563, 2)
    assert source['table_origins']['income_cases'] == 'authored_assumption'


def test_reference_and_ordered_prefix_alternative_across_controls():
    _, data = inputs()
    for name, _, changed in [('original', '', data), *controls(data)]:
        expected = calculate(changed)
        equal(execute(changed, SQL), expected)
        equal(execute(changed, alternatives()), expected)
        income_cases = {r['income_case']: r['income'] for r in changed['income_cases']}
        prices = {r['price_case']: r['price'] for r in changed['price_cases']}
        for price, income, _, eps in expected['diluted_eps']:
            exact = min(e for e, _ in independent_subsets(changed, prices[price], income_cases[income]))
            assert eps == pytest.approx(float(exact), rel=0, abs=1e-12), name


def test_settlement_values_and_independent_price_root():
    _, data = inputs()
    for name, _, changed in [('original', '', data), *controls(data)]:
        answer = calculate(changed)
        prices = {r['price_case']: fraction(r['price']) for r in changed['price_cases']}
        for price_case, price in prices.items():
            issuance = sum(row[3] for row in answer['settlement_scenarios'] if row[0] == price_case)
            assert issuance == pytest.approx(float(independent_gross(changed, price)), rel=0, abs=1e-12), name
        lower, upper = Fraction(1, 100), Fraction(1000)
        target = fraction(changed['threshold_case'][0]['target_shares'])
        assert independent_gross(changed, lower) < target < independent_gross(changed, upper)
        for _ in range(70):
            midpoint = (lower + upper) / 2
            if independent_gross(changed, midpoint) < target:
                lower = midpoint
            else:
                upper = midpoint
        expected = dict(answer['thresholds'])['share_price']
        assert expected == pytest.approx(float((lower + upper) / 2), rel=0, abs=1e-10), name


def test_portfolio_earnings_boundaries_change_inclusion_on_both_sides():
    _, data = inputs()
    for name, _, changed in [('original', '', data), *controls(data)]:
        price = changed['threshold_case'][0]['price']
        for measure, value in calculate(changed)['thresholds']:
            if not measure.startswith('earnings_'):
                continue
            note = measure.removeprefix('earnings_')
            for sign in [-1, 1]:
                income = fraction(value) + Fraction(sign, 10000)
                candidates = independent_subsets(changed, price, income)
                with_note = min(e for e, subset in candidates if note in subset)
                without_note = min(e for e, subset in candidates if note not in subset)
                assert (with_note < without_note) == (sign == 1), (name, note, sign)


def test_control_invariances_and_economic_decisions():
    _, data = inputs()
    answers = {name: calculate(changed) for name, _, changed in controls(data)}
    baseline = calculate(data)
    equal(answers['row_order'], baseline)
    equal(answers['carrying_only'], baseline)
    assert answers['scale']['diluted_eps'] == baseline['diluted_eps']
    assert dict(answers['scale']['thresholds'])['share_price'] == dict(baseline['thresholds'])['share_price']
    assert dict(answers['target_shift']['thresholds'])['share_price'] > dict(baseline['thresholds'])['share_price']
    assert dict(answers['cash_principal']['thresholds'])['earnings_2027'] > dict(baseline['thresholds'])['earnings_2027']
    before = dict(baseline['thresholds'])
    after = dict(answers['dilution_order']['thresholds'])
    assert before['earnings_2027'] < before['earnings_2025']
    assert after['earnings_2025'] < after['earnings_2027']
    assert all(row[3] == 0 for row in answers['out_of_money']['settlement_scenarios'])
    at_55 = independent_subsets(data, 40, 55)
    optimum, included = min(at_55)
    assert included == ('2027', '2029')
    alone_2025 = next(e for e, subset in at_55 if subset == ('2025',))
    without_notes = next(e for e, subset in at_55 if subset == ())
    assert alone_2025 < without_notes
    assert optimum < next(e for e, subset in at_55 if subset == ('2025', '2027', '2029'))
    assert min(e for e, _ in independent_subsets(data, 12, 73.714)) < fraction(73.714) / fraction(57.436)
    unchanged = copy.deepcopy(data)
    next(r for r in unchanged['notes'] if r['note'] == '2029')['amortization'] = 10
    equal(calculate(unchanged), baseline)


def test_exact_neutrality_does_not_grade_arbitrary_inclusion():
    _, data = inputs()
    tie = next(changed for name, _, changed in controls(data) if name == 'neutrality_tie')
    candidates = independent_subsets(tie, 10, 5.5)
    assert min(e for e, _ in candidates) == Fraction(1, 2)
    assert {tuple(n for n in subset if n != '2029') for e, subset in candidates if e == Fraction(1, 2)} == {(), ('2027',)}
    assert all('included' not in column for declaration in specification()['tables'].values() for column in declaration['columns'])


def test_targeted_wrong_submissions_fail_numerically():
    _, data = inputs()
    expected = calculate(data)
    for name, mistake in mistakes().items():
        table = mistake['table']
        assert mistake['sql'] != SQL[table], name
        actual = execute(data, {table: mistake['sql']})
        with pytest.raises(AssertionError):
            equal(actual, {table: expected[table]})


def test_interface_and_sql_limits():
    contract = specification()
    assert len(contract['tables']) == 3
    assert len(calculate(inputs()[1])['diluted_eps']) == 20
    for table in contract['tables'].values():
        assert len(table['columns']) <= 16
    for query in [*SQL.values(), *alternatives().values(), *(m['sql'] for m in mistakes().values())]:
        assert len(query.encode()) < 16384
