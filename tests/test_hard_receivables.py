"""Cash-conservation and financing-substance checks for the NER case."""
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from workflow_hard_receivables import SQL, alternatives, calculate, controls, mistakes, specification


def inputs():
    source = json.loads((ROOT/'datasets/workflow-hard-eval-v1/sources/constellation-2025.json').read_text())
    data = {name:[dict(zip(table['columns'],row)) for row in table['rows']]
            for name,table in source['tables'].items()}
    return source,data


def run_sql(data, queries):
    source,_ = inputs()
    with sqlite3.connect(':memory:') as connection:
        for name,rows in data.items():
            columns = source['tables'][name]['columns']
            connection.execute('CREATE TABLE '+name+' ('+','.join(k+' '+v for k,v in columns.items())+')')
            connection.executemany('INSERT INTO '+name+' VALUES ('+','.join('?' for _ in columns)+')',
                                   [tuple(row[k] for k in columns) for row in rows])
        return {name:[list(row) for row in connection.execute(query)] for name,query in queries.items()}


def equal(actual, expected):
    assert actual.keys() == expected.keys()
    for table in expected:
        assert len(actual[table]) == len(expected[table])
        for a,b in zip(sorted(actual[table]),sorted(expected[table])):
            for x,y in zip(a,b):
                assert x == y if isinstance(y,str) else x == pytest.approx(y,rel=0,abs=1e-9)


def test_source_integrity_and_scope():
    source,data = inputs()
    expected = source.pop('extract_sha256')
    assert hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest() == expected
    assert len(source['captures']) == 2
    assert {c['url'] for c in source['captures']} == {e['source_url'] for e in source['evidence'] if e['source_url'].startswith('https:')}
    assert all(len(c['sha256']) == 64 and c['bytes'] > 0 and c['redistributed'] is False for c in source['captures'])
    assert all('source_url' in e and 'publication_date' in e for e in source['evidence'])
    assert data['cash_flows'][0]['operating'] == -1448
    assert data['cash_flows'][1]['operating'] == 3432
    assert data['cash_flows'][1]['operating'] != 3332
    assert data['other_sales'][1]['gross_receivables_sold'] == 3207
    assert data['transition'][0]['as_of'] > '2024-09-30'


def test_original_outcomes_and_all_sql_routes():
    _,data = inputs()
    result = calculate(data)
    assert result == {
        'cashflow_recast':[['2024-9m',5956,-2048,-2480,1428],['2025-9m',3432,-2221,-249,962]],
        'cash_generation_change':[[4880,-2524,7404,-1687,-837,-2651,-964]],
        'retained_interest_bridge':[['2024-9m',7682,-300,550,578,-28]]}
    for name,_,changed in [('original','',data),*controls(data)]:
        expected = calculate(changed)
        equal(run_sql(changed,SQL),expected)
        equal(run_sql(changed,alternatives()),expected)


def test_independent_receivable_pool_and_treasury_model():
    _,data = inputs()
    F = lambda v:Fraction(str(v))
    for name,_,changed in [('original','',data),*controls(data)]:
        answer = calculate(changed)
        f = changed['facility_flows'][0]
        opening,closing = sorted(changed['facility_balances'],key=lambda r:r['sequence'])
        assert F(f['new_transfer_cash'])+F(f['dpp_collections']) == F(f['cash_reinvested'])
        assert F(closing['purchaser_funding'])-F(opening['purchaser_funding']) == -F(f['purchaser_payment'])
        for balance in [opening,closing]:
            assert F(balance['pool_fair_value']) == F(balance['purchaser_funding'])+F(balance['dpp'])
        pool_delta = F(closing['pool_fair_value'])-F(opening['pool_fair_value'])
        transaction_delta = F(f['receivables_sold'])-F(f['cash_reinvested'])
        assert float(pool_delta-transaction_delta) == answer['retained_interest_bridge'][0][-1], name
        cash_by_period = {r['period']:r for r in changed['cash_flows']}
        for period,operating,investing,financing,total in answer['cashflow_recast']:
            original = cash_by_period[period]
            assert total == original['net_cash_change']
            assert F(operating)+F(investing)+F(financing) == F(total)
            assert sum(F(original[k]) for k in ['operating','investing','financing']) == F(total)
        old = cash_by_period[f['period']]
        assert F(old['net_dpp_investing']) == F(f['dpp_collections'])-F(f['purchaser_payment'])
        # Replacing the old program's paired OCF/ICF cash with customer receipts
        # plus net purchaser capital preserves treasury cash.
        old_cash = F(f['new_transfer_cash'])+F(old['net_dpp_investing'])
        modeled_cash = F(f['cash_reinvested'])-F(f['purchaser_payment'])
        assert old_cash == modeled_cash


def test_controls_preserve_cash_economics_and_change_dependencies():
    _,data = inputs()
    baseline = calculate(data)
    results = {name:calculate(changed) for name,_,changed in controls(data)}
    equal(results['row_order'],baseline)
    for table,rows in results['scale'].items():
        for row,original in zip(rows,baseline[table]):
            assert row == [v if isinstance(v,str) else v*2 for v in original]
    for name in ['noncash_originations','unallocated_movement']:
        assert results[name]['cashflow_recast'] == baseline['cashflow_recast']
        assert results[name]['cash_generation_change'] == baseline['cash_generation_change']
    assert results['noncash_originations']['retained_interest_bridge'][0][-1] == -28
    assert results['unallocated_movement']['retained_interest_bridge'][0][-1] == -8
    assert results['funding_draw']['cashflow_recast'][0][1] == baseline['cashflow_recast'][0][1]
    assert results['funding_draw']['cashflow_recast'][0][3] == -1980
    assert results['customer_collection']['cashflow_recast'][0][1] == 6056
    assert results['customer_collection']['retained_interest_bridge'][0][-1] == -28
    assert results['collateral_cash']['cash_generation_change'][0][4] == -837
    assert results['capex_cash']['cash_generation_change'][0][1] == -2524
    assert results['capex_cash']['cash_generation_change'][0][-1] == -1014


def test_non_cash_transition_and_other_sales_do_not_define_ner_cash():
    _,data = inputs()
    result = calculate(data)
    changed = copy.deepcopy(data)
    changed['transition'][0]['dpp_reassigned'] += 500
    changed['other_sales'][1]['gross_receivables_sold'] += 1000
    changed['credit_losses'][0]['loss_on_sale'] += 10
    equal(calculate(changed),result)


def test_targeted_mistakes_fail_for_numeric_reasons():
    _,data = inputs()
    expected = calculate(data)
    for name,mistake in mistakes().items():
        table = mistake['table']
        assert mistake['sql'] != SQL[table],name
        with pytest.raises(AssertionError):
            equal(run_sql(data,{table:mistake['sql']}),{table:expected[table]})


def test_output_limits_and_sufficient_alternative_evidence():
    spec = specification()
    assert len(spec['tables']) == len(spec['claims']) == 3
    assert ['c01:s02','c01:s05','c01:s07'] in spec['tables']['retained_interest_bridge']['evidence']
    assert ['c01:s04'] in spec['claims']['claim_3']['evidence']
    assert all(len(t['columns']) <= 16 for t in spec['tables'].values())
    for sql in [*SQL.values(),*alternatives().values(),*(m['sql'] for m in mistakes().values())]:
        assert len(sql.encode()) < 16384
