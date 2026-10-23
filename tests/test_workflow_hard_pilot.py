"""Source arithmetic, economic invariants and sharpness for the experimental tier."""
from decimal import Decimal
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_workflow_hard_pilot import DATASET, construct, source_data
from workflow_hard_cases import specifications, controls, vertices
from workpaperbench.catalog import load, tree_hash

D=lambda x:Decimal(str(x))


def inputs(key):
    s=specifications()[key]
    source=json.loads((ROOT/'datasets'/DATASET/'sources'/(s['source']+'.json')).read_text())
    data=source_data(source)
    if key=='c01':
        data['stress_rates']=[{'geography':g,'products_loss_pct':p,'services_loss_pct':v}
                             for g,p,v in [('us',5,2),('china',25,10),('other',12,3)]]
    return s,data


def test_frozen_identity_and_candidate_separation():
    m=load(ROOT,DATASET)
    assert len(m['tasks'])==3
    for k,spec in m['tasks'].items():
        assert spec['split']=='development'
        _,_,task=load(ROOT,DATASET,k)
        assert set(p.name for p in (task/'environment').iterdir())=={
            'Dockerfile','data.sqlite','schema.json','sources.md','evidence.json','output_contract.json'}
        assert 'COPY data.sqlite evidence.json sources.md schema.json output_contract.json /workspace/' in (task/'environment/Dockerfile').read_text()
        assert (task/'tests/workpaperbench/workflow_grading.py').read_bytes()==(ROOT/m['scorer_path']).read_bytes()
        assert (task/'tests/workpaperbench/workflow_sql_worker.py').read_bytes()==(ROOT/m['sql_worker_path']).read_bytes()
        assert (task/'tests/data.sqlite').read_bytes()==(task/'environment/data.sqlite').read_bytes()
        assert (task/'task.toml').read_text().replace(DATASET+'-'+k,'workflow-v15-c01')==(ROOT/'datasets/workflow-v15/tasks/c01/task.toml').read_text()
        source=json.loads((ROOT/'datasets'/DATASET/'sources'/(spec['source_group']+'.json')).read_text())
        expected=source.pop('extract_sha256')
        assert hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==expected


def test_reconstruct_all_bytes(tmp_path):
    if sqlite3.sqlite_version!='3.45.1': pytest.skip('Pinned database builder requires supported SQLite 3.45.1 controller')
    assert construct(tmp_path)==load(ROOT,DATASET)
    assert tree_hash(tmp_path/'tasks')==tree_hash(ROOT/'datasets'/DATASET/'tasks')


def test_frozen_scorer_rejects_contract_mistakes():
    m=load(ROOT,DATASET)
    module_spec=importlib.util.spec_from_file_location('workpaperbench.hard_frozen_scorer',ROOT/m['scorer_path'])
    scorer=importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(scorer)
    for key in m['tasks']:
        _,_,task=load(ROOT,DATASET,key)
        gold=json.loads((task/'tests/gold.json').read_text())
        for declaration in gold['tables'].values():
            original={'columns':list(declaration['columns']),'rows':declaration['rows']}
            def error(rows):
                return scorer.comparison_error({'columns':original['columns'],'rows':rows},declaration,original['rows'])
            assert error(original['rows']) is None
            assert error(original['rows'][:-1])=='rows'
            if len(original['rows'])>1:
                duplicate=copy.deepcopy(original['rows'])
                duplicate[-1]=duplicate[0]
                assert error(duplicate)=='keys'
                swapped=copy.deepcopy(original['rows'])
                for name in declaration['keys']:
                    i=original['columns'].index(name)
                    swapped[0][i],swapped[1][i]=swapped[1][i],swapped[0][i]
                assert error(swapped)=='numeric'
            for i,column in enumerate(declaration['columns'].values()):
                if column['type']=='text': continue
                wrong=copy.deepcopy(original['rows'])
                nonzero=next((j for j,row in enumerate(wrong) if row[i]),None)
                if nonzero is None: continue
                wrong[nonzero][i]/=100 if column['unit']=='percent' else 1000
                assert error(wrong)=='numeric'


def test_ahold_independent_period_derivation_and_controls():
    s,data=inputs('a01')
    base=s['calculate'](data)
    assert base['annual_change_bridge'][0][:4]==[11492,-10042,745,2195]
    # Independently published adjusted FY2015 columns, excluded from candidate
    # targets, verify the reconstructed extra-week treatment.
    prior={r[0]:r[3] for r in base['comparable_periods'] if r[1]=='fy'}
    assert prior==dict(zip(['ahold_usa','delhaize_america','netherlands','belgium','cse'],[22654,15146,12362,4859,5115]))
    assert sum(r[4] for r in base['comparable_periods'] if r[1]=='pre_q4')==1612
    for name,_,d in controls('a01',data):
        answer=s['calculate'](d)
        p={r['segment']:r for r in d['period_sales']}
        for row in answer['comparable_periods']:
            if row[1]=='pre_q4':
                assert row[3]==p[row[0]]['fy2015']-p[row[0]]['q42015']
        if name in ['calendar_extension','divestment_scope','prior_extra_week']:
            assert [r for r in answer['comparable_periods'] if r[1]=='pre_q4']==[r for r in base['comparable_periods'] if r[1]=='pre_q4']
        if name=='independent_reported_discrepancy': assert answer['annual_change_bridge'][0][-1]==-7


def test_microsoft_gross_accumulated_derivation_and_controls():
    s,data=inputs('b01')
    baseline=s['calculate'](data)
    assert baseline['ppe_bridge'][0]==[2600,67151,20511,22000,69375,65662,3713]
    for name,_,d in [('original','',data),*controls('b01',data)]:
        answer=s['calculate'](d)
        p={r['year']:r for r in d['ppe']}
        f={r['year']:r for r in d['finance_leases']}
        a=d['annual_expenses'][0]
        for population in (p,f):
            for r in population.values(): assert r['gross']-r['accumulated']==r['net']
        gross_residual=D(p[2025]['gross'])-D(p[2024]['gross'])-D(d['cash_flows'][0]['cash_ppe'])-1000*(D(p[2025]['capital_payables_billion'])-D(p[2024]['capital_payables_billion']))-D(a['finance_rou_additions'])
        accumulated_residual=D(p[2025]['accumulated'])-D(p[2024]['accumulated'])-1000*D(a['ppe_depreciation_billion'])
        assert float(gross_residual-accumulated_residual)==answer['ppe_bridge'][0][-1]
        if name in ['payable_settlement','noncash_lease','principal_settlement','other_cf_adjustment']:
            assert answer['ppe_bridge'][0][-1]==baseline['ppe_bridge'][0][-1]
        if name in ['noncash_lease','other_cf_adjustment','unallocated_asset_movement']:
            assert answer['cash_investment'][0][2]==baseline['cash_investment'][0][2]


def greedy_certificate(data, measure, lower):
    lines={r['business_line']:r for r in data['business_lines']}
    rates={r['geography']:r for r in data['stress_rates']}
    margins={k:(D(v['net_sales'])-D(v['cost_of_sales']))/D(v['net_sales']) for k,v in lines.items()}
    weights={k:D(1) for k in lines} if measure=='revenue' else margins
    capacities={r['geography']:D(r['net_sales']) for r in data['geographies']}
    slopes={g:(D(rates[g]['products_loss_pct'])*weights['products']-D(rates[g]['services_loss_pct'])*weights['services'])/100 for g in capacities}
    remaining=D(lines['services']['net_sales'])
    allocation={}
    for g in sorted(capacities,key=lambda x:slopes[x],reverse=lower):
        allocation[g]=min(remaining,capacities[g])
        remaining-=allocation[g]
    assert remaining==0
    assert sum(capacities[g]-allocation[g] for g in capacities)==D(lines['products']['net_sales'])
    assert all(0<=allocation[g]<=capacities[g] for g in capacities)
    # Exchange optimality certificate: an occupied lower-priority cell cannot
    # improve the objective by transferring Services into unused capacity.
    for g in capacities:
        for h in capacities:
            if allocation[g]>0 and allocation[h]<capacities[h]:
                assert slopes[g]>=slopes[h] if lower else slopes[g]<=slopes[h]
    loss=sum(((capacities[g]-allocation[g])*D(rates[g]['products_loss_pct'])*weights['products']+
               allocation[g]*D(rates[g]['services_loss_pct'])*weights['services'])/100 for g in capacities)
    return loss,allocation


def test_apple_sharpness_feasibility_and_independent_optimization():
    s,data=inputs('c01')
    for name,_,d in [('original','',data),*controls('c01',data)]:
        answer=s['calculate'](d)
        for row in answer['stress_bounds']:
            for index,lower in [(1,True),(2,False)]:
                loss,allocation=greedy_certificate(d,row[0],lower)
                assert row[index]==pytest.approx(float(loss),abs=1e-8)
        if name=='original':
            revenue=greedy_certificate(d,'revenue',True)[1]
            profit=greedy_certificate(d,'gross_profit',True)[1]
            assert revenue=={'china':D(66952),'other':D(29217),'us':D(0)}
            assert profit=={'china':D(0),'other':D(96169),'us':D(0)}
            assert revenue!=profit
            assert answer['stress_bounds'][0][1:3]==pytest.approx([33001.91,42789.17])
            assert answer['stress_bounds'][1][1:3]==pytest.approx([14822.717151790983,16615.15312402922])
        for region in d['geographies']:
            total=sum(D(r['net_sales']) for r in d['geographies'])
            p=next(D(r['net_sales']) for r in d['business_lines'] if r['business_line']=='products')
            g=D(region['net_sales'])
            # Endpoint feasibility can also be checked by completing the
            # complementary countries, independently of the stress optimizer.
            for target in (max(D(0),p-(total-g)),min(p,g)):
                assert 0<=p-target<=total-g and 0<=target<=g
