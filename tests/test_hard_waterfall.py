"""Contractual priority, conversion incentives and sharp funding checks."""
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
from workflow_hard_waterfall import SQL, allocation, alternatives, calculate, controls, mistakes, specification


def inputs():
    source = json.loads((ROOT / 'datasets/workflow-hard-eval-v1/sources/reddit-2023.json').read_text())
    return source, {name: [dict(zip(t['columns'], r)) for r in t['rows']]
                    for name, t in source['tables'].items()}


def execute(data, queries):
    source, _ = inputs()
    with sqlite3.connect(':memory:') as c:
        for name, rows in data.items():
            columns = source['tables'][name]['columns']
            c.execute('CREATE TABLE '+name+' ('+','.join(k+' '+v for k,v in columns.items())+')')
            c.executemany('INSERT INTO '+name+' VALUES ('+','.join('?' for _ in columns)+')',
                          [tuple(row[k] for k in columns) for row in rows])
        return {name: [list(r) for r in c.execute(query)] for name, query in queries.items()}


def equal(actual, expected):
    assert actual.keys() == expected.keys()
    for name in expected:
        assert len(actual[name]) == len(expected[name])
        for actual_row, expected_row in zip(sorted(actual[name]), sorted(expected[name])):
            for a, e in zip(actual_row, expected_row):
                if isinstance(e, str):
                    assert a == e
                else:
                    assert a == pytest.approx(e, rel=0, abs=1e-8)


def f(value):
    return Fraction(str(value))


def independent_equilibria(data, proceeds):
    """Enumerate actual cash waterfalls and check every conversion deviation.

    This uses neither a common-price funding equation nor an ordered-prefix
    rule. Every prospective conversion pattern first pays the remaining claims
    by legal rank. A pattern survives only if no cohort can improve its cash
    by changing conversion status, with mandatory conversions imposed first.
    """
    terms = {r['series']: r for r in data['terms']}
    shares = {r['series']: f(r['shares']) / 1000000 for r in data['preferred']}
    claims = {name: count*f(terms[name]['issue_price'])*f(terms[name]['preference_multiple'])
              for name, count in shares.items()}
    forced = {name for name in shares if terms[name]['forced_eligible']
              and f(proceeds) > f(data['trigger'][0]['valuation'])}
    options = sorted(set(shares)-forced)
    pool = f(proceeds)
    outcomes = {}
    for flags in itertools.product([False, True], repeat=len(options)):
        converted = forced | {name for name, yes in zip(options, flags) if yes}
        remaining = set(shares)-converted
        cash = {name: Fraction(0) for name in shares}
        available = pool
        for rank in sorted({terms[name]['rank'] for name in remaining}):
            group = [name for name in remaining if terms[name]['rank'] == rank]
            total = sum(claims[name] for name in group)
            funded = min(available, total)
            for name in group:
                cash[name] = funded*claims[name]/total
            available -= funded
        denominator = sum(f(r['shares'])/1000000 for r in data['common'])
        denominator += sum(shares[name]*f(terms[name]['conversion_ratio']) for name in converted)
        for name in converted:
            cash[name] = available*shares[name]*f(terms[name]['conversion_ratio'])/denominator
        for row in data['common']:
            cash[row['security']] = available*f(row['shares'])/1000000/denominator
        outcomes[flags] = cash
    valid = []
    for flags, cash in outcomes.items():
        for i, name in enumerate(options):
            other = list(flags)
            other[i] = not other[i]
            if outcomes[tuple(other)][name] > cash[name]:
                break
        else:
            valid.append(cash)
    assert valid
    return valid


def test_sources_and_contract_values_are_distinct_from_book_values():
    source, data = inputs()
    expected = source.pop('extract_sha256')
    assert hashlib.sha256(json.dumps(source, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest() == expected
    assert len(source['captures']) == 2
    assert all(len(r['sha256']) == 64 and not r['redistributed'] for r in source['captures'])
    assert sum(r['shares'] for r in data['preferred']) == 73021449
    assert sum(r['shares'] for r in data['common']) == 61003904
    terms = {r['series']: r for r in data['terms']}
    a = next(r for r in data['preferred'] if r['series'] == 'A')
    assert f(a['shares'])*f(terms['A']['issue_price'])*f(terms['A']['preference_multiple'])/1000000 == f('35.0004375')
    assert a['carrying'] == 21.670
    e = next(r for r in data['preferred'] if r['series'] == 'E')
    # Preserve the disclosed difference rather than describing every difference
    # as a rounding residual or silently forcing contract values to match it.
    reconstructed = f(e['shares'])*f(terms['E']['issue_price'])/1000000
    assert f(e['reported_preference'])-reconstructed == f('0.0020324604')
    assert source['table_origins']['owner_targets'] == 'authored_assumption'


def test_reference_and_materially_different_sql_across_controls():
    _, data = inputs()
    for name, _, changed in [('original', '', data), *controls(data)]:
        expected = calculate(changed)
        equal(execute(changed, SQL), expected)
        equal(execute(changed, alternatives()), expected)
        for case in changed['sale_cases']:
            rows = [r for r in expected['sale_allocations'] if r[0] == case['sale_case']]
            assert sum(r[2] for r in rows) == pytest.approx(case['proceeds'], rel=0, abs=1e-9), name
            assert all(r[2] >= 0 for r in rows)


def test_independent_legal_priority_and_conversion_economics():
    _, data = inputs()
    for proceeds in [200, 240, 241, 1850, 2500, 4000, 9000]:
        equilibria = independent_equilibria(data, proceeds)
        expected, _ = allocation(data, proceeds)
        for equilibrium in equilibria:
            assert sum(equilibrium.values()) == f(proceeds)
            for security, cash in equilibrium.items():
                assert float(cash) == pytest.approx(float(expected[security]), rel=0, abs=1e-10)
    changed_inputs = {name: changed for name, _, changed in controls(data)}
    for name, proceeds_cases in [('trigger_higher', [1850, 2500]), ('conversion_ratio', [6000, 9000])]:
        changed = changed_inputs[name]
        for proceeds in proceeds_cases:
            expected, _ = allocation(changed, proceeds)
            for equilibrium in independent_equilibria(changed, proceeds):
                assert {k: float(v) for k, v in equilibrium.items()} == pytest.approx({k: float(v) for k, v in expected.items()}, rel=0, abs=1e-10)


def test_funding_endpoints_and_both_contractual_branches():
    _, data = inputs()
    for name, _, changed in [('original', '', data), *controls(data)]:
        targets = {r['target_case']: r for r in changed['owner_targets']}
        boundary = changed['trigger'][0]['valuation']
        for target_case, infimum, attained in calculate(changed)['owner_funding']:
            target = targets[target_case]
            security, amount = target['security'], target['cash_target']
            at, _ = allocation(changed, infimum)
            above, _ = allocation(changed, infimum+0.000001)
            below, _ = allocation(changed, infimum-0.000001)
            assert float(above[security]) >= amount, (name, target_case)
            assert float(below[security]) < amount, (name, target_case)
            if attained:
                assert float(at[security]) == pytest.approx(amount, rel=0, abs=1e-9)
            else:
                assert infimum == boundary and float(at[security]) < amount
            # Each branch has nondecreasing cash entitlements. If the selected
            # solution is after the trigger, the closed first branch must fail.
            if infimum > boundary:
                first_end, _ = allocation(changed, boundary)
                assert float(first_end[security]) < amount
    result = {r[0]: r[1:] for r in calculate(data)['owner_funding']}
    assert result['F_54'] == [240.0, 0]
    assert result['A_4'][0] < 240 < result['A_10'][0]


def test_conversion_frontiers_and_duplicate_economic_terms():
    _, data = inputs()
    for name, _, changed in [('original', '', data), *controls(data)]:
        terms = {r['series']: r for r in changed['terms']}
        counts = {r['series']: r['shares'] for r in changed['preferred']}
        for series, proceeds, price in calculate(changed)['conversion_frontiers']:
            at, common_price = allocation(changed, proceeds)
            assert float(common_price) == pytest.approx(price, rel=0, abs=1e-10), name
            preference = counts[series]/1000000*terms[series]['issue_price']*terms[series]['preference_multiple']
            assert float(at[series]) == pytest.approx(preference, rel=0, abs=1e-9)
            below, _ = allocation(changed, proceeds-0.00001)
            above, _ = allocation(changed, proceeds+0.00001)
            assert float(below[series]) == pytest.approx(preference, rel=0, abs=1e-9)
            assert float(above[series]) > preference
    frontiers = {r[0]: r[1:] for r in calculate(data)['conversion_frontiers']}
    assert frontiers['D'] == frontiers['D-1']
    assert frontiers['F'] == frontiers['F-1']
    assert all('converted' not in c for t in specification()['tables'].values() for c in t['columns'])


def test_invariances_and_intended_analytical_mistakes():
    _, data = inputs()
    baseline = calculate(data)
    control_data = {name: changed for name, _, changed in controls(data)}
    for name in ['row_order', 'carrying_only']:
        equal(calculate(control_data[name]), baseline)
    doubled = calculate(control_data['scale'])
    for original, scaled in zip(baseline['sale_allocations'], doubled['sale_allocations']):
        assert scaled[:2] == original[:2]
        assert scaled[2] == original[2]*2 and scaled[3] == original[3]
    for original, scaled in zip(baseline['owner_funding'], doubled['owner_funding']):
        assert scaled == [original[0], original[1]*2, original[2]]
    a240 = next(r[2] for r in baseline['sale_allocations'] if r[:2] == ['v240', 'A'])
    a241 = next(r[2] for r in baseline['sale_allocations'] if r[:2] == ['v241', 'A'])
    assert a240 > 4.5 and a241 == 0
    ratio_answer = calculate(control_data['conversion_ratio'])
    e_cash_per_original = next(r[3] for r in ratio_answer['sale_allocations'] if r[:2] == ['v6000', 'E'])
    common_per_share = next(r[3] for r in ratio_answer['sale_allocations'] if r[:2] == ['v6000', 'common_A'])
    assert e_cash_per_original == pytest.approx(1.2*common_per_share, rel=0, abs=1e-10)
    for name, mistake in mistakes().items():
        table = mistake['table']
        assert mistake['sql'] != SQL[table], name
        changed = data
        expected = baseline
        if mistake.get('scope') == 'controls':
            equal(execute(data, {table: mistake['sql']}), {table: baseline[table]})
            changed = control_data['conversion_ratio']
            expected = calculate(changed)
        actual = execute(changed, {table: mistake['sql']})
        with pytest.raises(AssertionError):
            equal(actual, {table: expected[table]})


def test_interface_limits():
    spec = specification()
    assert len(spec['tables']) == len(spec['claims']) == 3
    for query in [*SQL.values(), *alternatives().values(), *(r['sql'] for r in mistakes().values())]:
        assert len(query.encode()) < 16384
