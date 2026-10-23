"""Accounting identities and cash classification checks for the BMS task."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from workflow_hard_acquisition import SQL,alternatives,calculate,controls,mistakes,specification


def inputs():
    source=json.loads((ROOT/'datasets/workflow-hard-eval-v1/sources/bms-2020.json').read_text())
    data={name:[dict(zip(t['columns'],row)) for row in t['rows']] for name,t in source['tables'].items()}
    return source,data


def execute(data,queries):
    source,_=inputs()
    with sqlite3.connect(':memory:') as db:
        for name,rows in data.items():
            columns=source['tables'][name]['columns']
            db.execute('CREATE TABLE '+name+' ('+','.join(k+' '+v for k,v in columns.items())+')')
            db.executemany('INSERT INTO '+name+' VALUES ('+','.join('?' for _ in columns)+')',
                           [tuple(row[k] for k in columns) for row in rows])
        return {name:[list(row) for row in db.execute(query)] for name,query in queries.items()}


def equal(actual,expected):
    assert actual.keys()==expected.keys()
    for name in expected:
        assert len(actual[name])==len(expected[name])
        for received,target in zip(sorted(actual[name]),sorted(expected[name])):
            for a,e in zip(received,target):
                assert a==e if isinstance(e,str) else a==pytest.approx(e,rel=0,abs=1e-7)


def number(x):
    return F(str(x))


def test_source_hash_and_scope():
    source,_=inputs()
    expected=source.pop('extract_sha256')
    assert hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':')).encode()).hexdigest()==expected
    assert source['capture_sha256']=='efa4071d4d0035a31313b35573a98b50d304aa14f0dd1bd86b9d11c7e53ae1bf'
    assert 'does not establish cash payment timing' in ' '.join(specification()['assumptions'])
    assert all(t['origin']=='authentic_source_facts' for t in source['tables'].values())


@pytest.mark.parametrize('variant',['original']+[c[0] for c in controls(inputs()[1])])
def test_references_and_independent_financial_identities(variant):
    _,original=inputs()
    versions={'original':original,**{name:data for name,_,data in controls(original)}}
    data=versions[variant]
    expected=calculate(data)
    equal(execute(data,SQL),expected)
    equal(execute(data,alternatives()),expected)
    # Acquired assets, liabilities and goodwill independently establish the basis.
    for row in data['acquisitions']:
        assets=sum((number(r['amount']) for r in data['allocated_assets'] if r['deal']==row['deal']),F(0))
        output=next(r for r in expected['acquisition_bases'] if r[0]==row['deal'])
        assert float(assets)==pytest.approx(output[1])
        assert float(assets-number(row['reported_basis']))==pytest.approx(output[2])
        # Purchase consideration and service compensation are distinct recipients.
        vested_awards=number(row['cash_awards'])-number(row['unvested_award_charge'])
        purchase_cash=number(row['cash_shares'])+vested_awards-number(row['cash_acquired'])
        assert float(purchase_cash)==pytest.approx(output[5])
    # Reconstruct the narrow earnings result directly from the full income statement,
    # excluding selected expenses rather than adding amounts to reported pretax income.
    lines={r['line']:number(r['amount']) for r in data['earnings_lines']}
    current=next(r for r in data['periods'] if r['year']==2020)
    effect=data['acquisition_effects'][0]
    expenses=lines['cost_of_products']+lines['amortization']
    expenses+=lines['sales_admin']-number(effect['sales_admin_award_charge'])
    expenses+=lines['research']-number(effect['research_award_charge'])
    expenses+=lines['other_expense']-number(current['contingent_fv_expense'])
    assert float(lines['revenue']-expenses)==pytest.approx(dict(expected['performance_views'])['selected_effects_excluded_pretax_usd_million'])
    assert float(lines['revenue']-sum(v for k,v in lines.items() if k!='revenue'))==pytest.approx(current['pretax'])
    # A cash-use ledger with compensation removed from CFO must equal the statutory
    # cash categories. This checks the classification as well as the arithmetic.
    for p in data['periods']:
        deal=next(a for a in data['acquisitions'] if a['year']==p['year'])
        gross=number(deal['cash_shares'])+number(deal['cash_awards'])-number(deal['cash_acquired'])
        compensation=number(deal['unvested_award_charge'])
        remainder=number(p['acquisition_payments'])-(gross-compensation)
        available=number(p['operating_cash'])+compensation-number(p['capex'])-gross-remainder+number(p['divestiture_proceeds'])
        assert float(available)==pytest.approx(next(r[-1] for r in expected['cash_coverage'] if r[0]==p['year']))


def test_known_results_and_independent_asset_identity():
    _,data=inputs()
    result=calculate(data)
    assert next(r for r in result['acquisition_bases'] if r[0]=='MyoKardia')==['MyoKardia',12660.0,0.0,0.0,12228.0,11746.0,12228.0]
    assert next(r for r in result['acquisition_bases'] if r[0]=='Celgene')==['Celgene',80269.0,0.0,44524.0,24566.0,24566.0,11166.0]
    assert result['cash_coverage']==[[2019,8210.0,24566.0,211.0,2452.0,-1551.0],[2020,14534.0,11746.0,1338.0,870.0,1085.0]]
    views=dict(result['performance_views'])
    assert views['immediate_myokardia_expenses_usd_million']==11920
    assert views['selected_effects_excluded_pretax_usd_million']==3292
    assert 11553+861+295+177-226==12660
    assert 11553-115==11438


def test_controls_preserve_economic_invariants():
    _,data=inputs()
    baseline=calculate(data)
    changed={name:calculate(d) for name,_,d in controls(data)}
    equal(changed['row_order'],baseline)
    # Reclassifying unchanged cash from purchase to compensation cannot change the
    # overall cash remainder or earnings when the corresponding IPRD cost falls.
    assert changed['compensation_classification']['performance_views']==baseline['performance_views']
    assert [r[-1] for r in changed['compensation_classification']['cash_coverage']]==[r[-1] for r in baseline['cash_coverage']]
    assert changed['accrued_transaction_cost']['cash_coverage']==baseline['cash_coverage']
    assert changed['noncash_remeasurement']['cash_coverage']==baseline['cash_coverage']
    assert changed['noncash_remeasurement']['performance_views']==baseline['performance_views']
    assert changed['share_valuation']['cash_coverage']==baseline['cash_coverage']
    assert changed['monetary_scale']['performance_views'][:2]==baseline['performance_views'][:2]


@pytest.mark.parametrize('name',list(mistakes()))
def test_targeted_mistakes_change_a_financial_result(name):
    _,data=inputs()
    mistake=mistakes()[name]
    wrong=execute(data,{mistake['table']:mistake['sql']})[mistake['table']]
    assert sorted(wrong)!=sorted(calculate(data)[mistake['table']])
