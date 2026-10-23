"""Financial feasibility, frozen packages and supported scoring for the evaluation supplement."""
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
from build_workflow_hard_evaluation import DATASET, construct, source_data
from workflow_hard_evaluation_cases import specifications, controls, alternatives
from workpaperbench.catalog import load, tree_hash

F=lambda x:Fraction(str(x))


def inputs(key):
    s=specifications()[key]
    source=json.loads((ROOT/'datasets'/DATASET/'sources'/(s['source']+'.json')).read_text())
    return s,source_data(source)


def test_frozen_packages_sources_and_separation():
    m=load(ROOT,DATASET)
    assert len(m['tasks'])==4
    for key,s in m['tasks'].items():
        assert s['split']=='evaluation'
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
                j=next((j for j,row in enumerate(wrong) if abs(row[i])>2*column.get('tolerance',0)),None)
                if j is not None:
                    wrong[j][i]/=1000
                    assert error(wrong)=='numeric'


def test_evaluation_source_groups_are_separate():
    current=load(ROOT,DATASET)
    groups={t['source_group'] for t in current['tasks'].values()}
    assert len(groups)==4
    for dataset in ['workflow-v15','workflow-hard-pilot-v1','workflow-hard-pilot-v2']:
        prior=load(ROOT,dataset)
        assert groups.isdisjoint({t['source_group'] for t in prior['tasks'].values()})
