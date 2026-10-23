"""Collateral certificate and funding-frontier financial checks."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path
import sqlite3
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from workflow_hard_borrowing_base import SQL, alternatives, calculate, controls, mistakes


def inputs():
    source=json.loads((ROOT/'datasets/workflow-hard-eval-v1/sources/albertsons-2025.json').read_text())
    data={n:[dict(zip(t['columns'],r)) for r in t['rows']] for n,t in source['tables'].items()}
    return source,data


def execute(data,queries):
    source,_=inputs()
    with sqlite3.connect(':memory:') as db:
        for n,rows in data.items():
            cols=source['tables'][n]['columns']
            db.execute('CREATE TABLE '+n+' ('+','.join(k+' '+v for k,v in cols.items())+')')
            db.executemany('INSERT INTO '+n+' VALUES ('+','.join('?' for _ in cols)+')',[tuple(r[k] for k in cols) for r in rows])
        return {n:[list(r) for r in db.execute(q)] for n,q in queries.items()}


def equal(actual,expected):
    assert actual.keys()==expected.keys()
    for name in actual:
        assert len(actual[name])==len(expected[name])
        for row,ref in zip(sorted(actual[name]),sorted(expected[name])):
            for a,e in zip(row,ref):
                assert a==e if isinstance(e,str) else a==pytest.approx(e,rel=0,abs=1e-7)


F=lambda x:Fraction(str(x))


def independent_certificate(f,c,seasonal,purchase=0):
    """Apply the source definitions as two counterfactual fixed points."""
    rate=F(f['seasonal_inventory_rate'] if seasonal else f['ordinary_inventory_rate'])
    regular=F(c['regular_inventory_cost'])+F(purchase)*F(c['regular_purchase_fraction'])
    perish=F(c['perishable_inventory_cost'])+F(purchase)*(1-F(c['regular_purchase_fraction']))
    u=F(f['receivable_rate'])*(F(c['credit_card_receivables'])+F(c['pharmacy_receivables']))+rate*regular*F(c['regular_appraisal'])
    p=rate*perish*F(c['perishable_appraisal'])
    s=F(f['script_rate'])*F(c['script_liquidation_value'])
    r=F(c['availability_reserves'])
    no_perish=no_shared=u+p+s-r
    for _ in range(80):
        no_perish=u+p+min(s,F(f['shared_dollar_cap']),F(f['shared_fraction'])*no_perish)-r
        no_shared=u+s+min(p,F(f['perishable_fraction'])*no_shared)-r
    return u+min(s,F(f['shared_dollar_cap']),F(f['shared_fraction'])*no_perish)+min(p,F(f['perishable_fraction'])*no_shared)-r


def test_sources_and_sql_across_controls():
    source,data=inputs()
    h=source.pop('extract_sha256')
    assert hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==h
    assert len(source['captures'])==2 and all(c['redistributed'] is False and len(c['sha256'])==64 for c in source['captures'])
    for name,_,changed in [('original','',data),*controls(data)]:
        expected=calculate(changed)
        equal(execute(changed,SQL),expected)
        equal(execute(changed,alternatives()),expected)
        cases={c['scenario']:c for c in changed['collateral_cases']}
        periods={p['period']:p['seasonal'] for p in changed['period_cases']}
        f=changed['facility_terms'][0]
        for scenario,period,_,base,_ in expected['certificates']:
            assert float(independent_certificate(f,cases[scenario],periods[period]))==pytest.approx(base,rel=0,abs=1e-9),name
        for scenario,period,maximum,base,surplus in expected['funding_limits']:
            c=cases[scenario];exposure=F(c['loans'])+F(c['letters_of_credit'])
            computed=independent_certificate(f,c,periods[period],maximum)
            assert float(computed)==pytest.approx(base,rel=0,abs=1e-9),name
            assert abs(surplus)<1e-7
            for offset in [Fraction(-1,10000),Fraction(1,10000)]:
                cost=F(maximum)+offset
                new_base=independent_certificate(f,c,periods[period],cost)
                feasible=exposure+cost<=min(F(f['commitment']),new_base)
                assert feasible==(offset<0),(name,scenario,period)


def test_invariance_and_actual_economic_constraints():
    _,data=inputs();baseline=calculate(data)
    changed={n:calculate(d) for n,_,d in controls(data)}
    equal(changed['row_order'],baseline)
    equal(changed['sublimits'],baseline)
    for name in baseline:
        for a,e in zip(sorted(changed['scale'][name]),sorted(baseline[name])):
            for i,(scaled,original) in enumerate(zip(a,e)):
                if isinstance(original,str) or (name=='purchase_plans' and i==6):assert scaled==original
                else:assert scaled==pytest.approx(2*original,rel=0,abs=1e-8)
    initial={(r[0],r[1]):r[4] for r in baseline['certificates']}
    assert all(r[2]>=initial[(r[0],r[1])] for r in baseline['funding_limits'])
    assert any(r[3]>4000 for r in baseline['certificates'])
    assert next(r for r in baseline['purchase_plans'] if r[:3]==['case_b','ordinary','plan_2'])[-1]==0
    assert next(r for r in baseline['funding_limits'] if r[:2]==['case_a','ordinary'])[2]>initial[('case_a','ordinary')]


def test_targeted_financial_mistakes():
    _,data=inputs();expected=calculate(data)
    for name,m in mistakes().items():
        table=m['table'];actual=execute(data,{table:m['sql']})
        with pytest.raises(AssertionError):equal(actual,{table:expected[table]})
