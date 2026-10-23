"""Financial feasibility, frozen packages and supported scoring for the follow-up tier."""
import copy
from fractions import Fraction
import hashlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import sqlite3
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_workflow_hard_followup import DATASET, construct, source_data
from workflow_hard_followup_cases import specifications, controls, alternatives
from workpaperbench.catalog import load, tree_hash

F=lambda x:Fraction(str(x))


def inputs(key):
    s=specifications()[key]
    source=json.loads((ROOT/'datasets'/DATASET/'sources'/(s['source']+'.json')).read_text())
    return s,source_data(source)


def test_frozen_packages_sources_and_separation():
    m=load(ROOT,DATASET)
    assert len(m['tasks'])==2
    for key,s in m['tasks'].items():
        assert s['split']=='development'
        _,_,task=load(ROOT,DATASET,key)
        assert {p.name for p in (task/'environment').iterdir()}=={
            'Dockerfile','data.sqlite','schema.json','sources.md','evidence.json','output_contract.json'}
        assert 'COPY data.sqlite evidence.json sources.md schema.json output_contract.json /workspace/' in (task/'environment/Dockerfile').read_text()
        assert (task/'tests/workpaperbench/workflow_grading.py').read_bytes()==(ROOT/m['scorer_path']).read_bytes()
        assert (task/'tests/workpaperbench/workflow_sql_worker.py').read_bytes()==(ROOT/m['sql_worker_path']).read_bytes()
        assert (task/'tests/data.sqlite').read_bytes()==(task/'environment/data.sqlite').read_bytes()
        assert (task/'task.toml').read_text().replace(DATASET+'-'+key,'workflow-v15-c01')==(ROOT/'datasets/workflow-v15/tasks/c01/task.toml').read_text()
        source=json.loads((ROOT/'datasets'/DATASET/'sources'/(s['source_group']+'.json')).read_text())
        expected=source.pop('extract_sha256')
        assert hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==expected
        assert all(len(sql.encode())<=16384 for sql in specifications()[key]['sql'].values())


def test_reproducible_build(tmp_path):
    if sqlite3.sqlite_version!='3.45.1': pytest.skip('Pinned SQLite 3.45.1 builder runs on the Linux controller')
    assert construct(tmp_path)==load(ROOT,DATASET)
    assert tree_hash(tmp_path/'tasks')==tree_hash(ROOT/'datasets'/DATASET/'tasks')


def vertices(constraints):
    """Intersect independent linear half-spaces a*d+b*y <= c exactly."""
    result=set()
    for (a,b,c,_),(p,q,r,_) in combinations(constraints,2):
        det=a*q-b*p
        if not det: continue
        d,y=(c*q-b*r)/det,(a*r-c*p)/det
        if all(u*d+v*y<=w for u,v,w,_ in constraints):
            result.add((d,y,all(not strict or u*d+v*y<w for u,v,w,strict in constraints)))
    return result


def financial_regions(data, row, equity_target=None):
    facility=data['facility'][0]
    c=F(facility['commitment'])-F(facility['utilised_including_lc'])
    t=F(facility['covenant_availability'])-F(facility['test_threshold'])
    rate=F(row['new_debt_cash_rate'])
    cash_generation=F(row['ebitda'])
    # These cash uses are economically different even where their coefficients coincide.
    cash_uses=sum(F(row[k]) for k in ('net_cash_capex','scheduled_principal','existing_cash_interest',
                                      'cash_tax','ordinary_dividend','working_capital_outflow'))
    numerator=F(row['ebitda'])-F(row['net_cash_capex'])
    denominator=sum(F(row[k]) for k in ('scheduled_principal','existing_cash_interest','cash_tax','ordinary_dividend'))
    common=[(-F(1),F(0),F(0),False),(F(1),F(0),c,False),(F(0),-F(1),F(0),False)]
    if equity_target is None:
        common.append((rate-1,F(1),cash_generation-cash_uses,False))
        covenant=(rate,F(1),numerator-denominator,False)
    else:
        common.append((rate-1,-F(1),cash_generation-cash_uses-equity_target,False))
        covenant=(rate,F(0),numerator-denominator-equity_target,False)
    return [common+[(F(1),F(0),t,True)], common+[(-F(1),F(0),-t,False),covenant]]


def extremum(regions, maximize):
    possibilities=set().union(*(vertices(region) for region in regions))
    best=(max if maximize else min)(y for _,y,_ in possibilities)
    return float(best),int(any(y==best and attained for _,y,attained in possibilities))


def test_covenant_independent_halfspace_financial_model():
    s,data=inputs('a01')
    for name,_,d in [('original','',data),*controls('a01',data)]:
        answer=s['calculate'](d)
        for row in d['planning_cases']:
            expected=extremum(financial_regions(d,row),True)
            actual=next(r for r in answer['distribution_frontier'] if r[0]==row['scenario'])
            assert actual[1]==pytest.approx(expected[0],abs=1e-8)
            assert actual[2]==expected[1]
            for target in d['equity_targets']:
                expected=extremum(financial_regions(d,row,F(target['special_dividend'])),False)
                actual=next(r for r in answer['equity_support'] if r[:2]==[row['scenario'],target['target']])
                assert actual[2]==pytest.approx(expected[0],abs=1e-8)
                assert actual[3]==expected[1]
        if name=='original':
            assert answer['distribution_frontier']==[['case_a',889.72,0],['case_b',1036.0,1],['case_c',1127.08,1]]
            assert answer['proposal_tests'][0][-2:]==[0,1]
            assert answer['proposal_tests'][0][4]<1


def test_covenant_invariances():
    s,data=inputs('a01')
    base=s['calculate'](data)
    for name,_,d in controls('a01',data):
        actual=s['calculate'](d)
        if name in ('suppressed_and_lc_context','row_order'):
            assert {k:sorted(v) for k,v in actual.items()}=={k:sorted(v) for k,v in base.items()}
        if name=='monetary_scale':
            for table,rows in base.items():
                numeric={'proposal_tests':(2,3),'distribution_frontier':(1,),'equity_support':(2,)}[table]
                for old,new in zip(rows,actual[table]):
                    for i,value in enumerate(old):
                        assert new[i]==pytest.approx(2*value) if i in numeric else new[i]==value


def test_reference_and_alternative_sql_all_inputs():
    # Only project-authored trusted SQL is executed here. Candidate workpapers
    # are checked separately in native isolated verifiers.
    for key,s in specifications().items():
        _,data=inputs(key)
        schemas=json.loads((ROOT/'datasets'/DATASET/'sources'/(s['source']+'.json')).read_text())['tables']
        for control,_,changed in [('original','',data),*controls(key,data)]:
            with sqlite3.connect(':memory:') as db:
                for name,rows in changed.items():
                    columns=list(rows[0])
                    db.execute('CREATE TABLE '+name+' ('+','.join(c+' '+schemas[name]['columns'][c] for c in columns)+')')
                    db.executemany('INSERT INTO '+name+' VALUES ('+','.join('?' for _ in columns)+')',
                                   [tuple(row[c] for c in columns) for row in rows])
                expected=s['calculate'](changed)
                for sqls in (s['sql'],alternatives(key)):
                    for name,sql in sqls.items():
                        cursor=db.execute(sql)
                        columns=[r[0] for r in cursor.description]
                        ordered=list(s['tables'][name]['columns'])
                        actual=sorted([row[columns.index(col)] for col in ordered] for row in cursor.fetchall())
                        for got,wanted in zip(actual,sorted(expected[name]),strict=True):
                            for g,w in zip(got,wanted,strict=True):
                                assert (g==w if isinstance(w,str) else g==pytest.approx(w,abs=1e-7)), (key,control,name,got,wanted)


def test_frozen_scorer_shape_units_and_evidence():
    m=load(ROOT,DATASET)
    module=importlib.util.spec_from_file_location('workpaperbench.followup_scorer',ROOT/m['scorer_path'])
    scorer=importlib.util.module_from_spec(module)
    module.loader.exec_module(scorer)
    for key in m['tasks']:
        _,_,task=load(ROOT,DATASET,key)
        gold=json.loads((task/'tests/gold.json').read_text())
        for spec in gold['tables'].values():
            cols=list(spec['columns'])
            def error(rows): return scorer.comparison_error({'columns':cols,'rows':rows},spec,spec['rows'])
            assert error(spec['rows']) is None
            assert error(spec['rows'][:-1])=='rows'
            if len(spec['rows'])>1:
                wrong=copy.deepcopy(spec['rows'])
                wrong[-1]=wrong[0]
                assert error(wrong)=='keys'
            for i,column in enumerate(spec['columns'].values()):
                if column['type']!='real': continue
                wrong=copy.deepcopy(spec['rows'])
                j=next((j for j,row in enumerate(wrong) if row[i]),None)
                if j is not None:
                    wrong[j][i]/=1000
                    assert error(wrong)=='numeric'
