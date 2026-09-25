"""Offline packaging of the expanded financial-workflow suite."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from workpaperbench.catalog import content_hash, load, tree_hash
from build_workflow_tasks import write_json
from workflow_development_cases import specifications, controls
from workflow_evaluation_cases import specifications as evaluation_specifications, controls as evaluation_controls

DATASET = 'workflow-v2'
OBSERVATIONS = ROOT / 'datasets/workflow-v2/observations'
TEMPLATE = ROOT / 'datasets/workflow-v1/tasks/b01'


def database(path,data):
    connection=sqlite3.connect(path)
    for name,rows in data.items():
        columns=list(rows[0])
        types=['REAL' if isinstance(rows[0][name],(int,float)) else 'TEXT' for name in columns]
        connection.execute('CREATE TABLE "'+name+'" ('+','.join('"'+column+'" '+kind for column,kind in zip(columns,types))+')')
        connection.executemany('INSERT INTO "'+name+'" VALUES ('+','.join('?' for _ in columns)+')',
                               [[row[column] for column in columns] for row in rows])
    connection.commit()
    connection.close()


def package(destination,key,spec):
    task=destination/'tasks'/key
    for name in ('environment','tests','solution'):(task/name).mkdir(parents=True)
    source=OBSERVATIONS/spec['source']
    data=json.loads((source/'facts.json').read_text())
    identifier=DATASET+'-'+key
    for folder in ('environment','tests'):
        database(task/folder/'data.sqlite',data)
        for name in ('sources.md','evidence.json'):shutil.copyfile(source/name,task/folder/name)
        shutil.copyfile(TEMPLATE/'environment/schema.json',task/folder/'schema.json')
    public_tables={name:{field:value for field,value in declaration.items() if field!='evidence'} for name,declaration in spec['tables'].items()}
    write_json(task/'environment/output_contract.json',{'tables':public_tables,
        'claim_assertions':{name:claim['assertion'] for name,claim in spec['claims'].items()},'definitions':spec['definitions']})
    starting=dict(spec['sql'])
    if key=='a02':starting['cash_model']=starting['cash_model'].replace('ocf-pp-lease','ocf-pp')
    elif key=='b02':starting['treasury_valuation']=starting['treasury_valuation'].replace('SUM(fair_value_usd) fv','SUM(par_usd) fv')
    elif key=='c02':starting['arr_guidance_bridge']=starting['arr_guidance_bridge'].replace('c.amount_usd_billion*(1+t.value/100.0)','p.amount_usd_billion*(1+t.value/100.0)')
    starting.update(spec.get('starting',{}))
    for name,sql in starting.items():(task/'environment'/('starting_'+name+'.sql')).write_text(sql+'\n')
    gold={'task_id':identifier,'scorer_version':'workflow-1.0.0','tables':copy.deepcopy(spec['tables']),
          'claims':{name:{field:value for field,value in claim.items() if field!='assertion'} for name,claim in spec['claims'].items()},
          'controls':[],'hashes':{},'context_evidence_allowed':[]}
    for name,rows in spec['calculate'](data).items():gold['tables'][name]['rows']=rows
    counterfactuals=evaluation_controls if spec.get('split')=='evaluation' else controls
    for number,(name,changed) in enumerate(counterfactuals(key,data),1):
        filename='control-'+str(number)+'.sqlite'
        database(task/'tests'/filename,changed)
        gold['controls'].append({'name':name,'database':filename,'origin':'authored_synthetic_counterfactual','tables':spec['calculate'](changed)})
    shutil.copytree(TEMPLATE/'tests/workpaperbench',task/'tests/workpaperbench')
    for name in ('Dockerfile','docker-compose.yaml','test.sh','verify.py'):shutil.copyfile(TEMPLATE/'tests'/name,task/'tests'/name)
    gold['hashes']={p.relative_to(task/'tests').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (task/'tests').rglob('*') if p.is_file()}
    write_json(task/'tests/gold.json',gold)
    reference={'task_id':identifier,'tables':[{'id':name,'file':name+'.sql','evidence':declaration['evidence'][0]} for name,declaration in spec['tables'].items()],
               'claims':[{'id':name,'verdict':claim['verdict'],'evidence':claim['evidence'][0]} for name,claim in spec['claims'].items()]}
    write_json(task/'tests/reference.json',reference)
    solve='#!/bin/bash\nset -euo pipefail\n'
    for name,sql in spec['sql'].items():
        (task/'solution'/(name+'.sql')).write_text(sql+'\n')
        solve+="cat > /logs/artifacts/"+name+".sql <<'SQL'\n"+sql+'\nSQL\n'
    solve+="cat > /logs/artifacts/answer.json <<'ANSWER'\n"+json.dumps(reference,indent=2)+'\nANSWER\n'
    (task/'solution/solve.sh').write_text(solve)
    files=' '.join(['data.sqlite','evidence.json','sources.md','schema.json','output_contract.json',*('starting_'+name+'.sql' for name in starting)])
    (task/'environment/Dockerfile').write_text((TEMPLATE/'environment/Dockerfile').read_text().split('COPY ',1)[0]+'COPY '+files+' /workspace/\n')
    (task/'task.toml').write_text((TEMPLATE/'task.toml').read_text().replace('workflow-v1-b01',identifier))
    contract=(TEMPLATE/'instruction.md').read_text().split('Read the source headings',1)[1].split('Recompute from pristine inputs.',1)[0]
    instruction='# Financial workflow\n\n'+spec['request']+'\n\nRead the source headings'+contract
    instruction+='Recompute from pristine inputs. Reviewed synthetic controls exercise equivalent scaling, component changes and behavior preservation. Later disclosures outside the requested periods do not change the requested outputs.\n\nTask ID: '+identifier+'\n'
    (task/'instruction.md').write_text(instruction)
    snapshots=json.loads((source/'snapshot.json').read_text())
    source_group=(snapshots[0] if isinstance(snapshots,list) else snapshots)['source_group']
    split=spec.get('split','development')
    write_json(task/'authoring.json',{'rationale':spec['rationale'],'source_group':source_group,'split':split,
        'exposure':'Reference/control verification only, no candidate-model exposure' if split=='evaluation' else 'Newly authored development case, never held out','observations':'authentic primary disclosures',
        'starting_defects':'authored synthetic work-product defects','controls':'authored synthetic counterfactuals',
        'reference_method':'Independent Python Decimal calculations from source facts, separate from submitted SQL','human_review':'pending',
        'source_snapshot_sha256':hashlib.sha256((source/'snapshot.json').read_bytes()).hexdigest(),
        'candidate_view_review':'Source headings, signs, periods and relevant definitions directly inspected before model exposure'})
    return source_group


def construct(destination):
    original=load(ROOT,'workflow-v1')
    manifest={'dataset_id':DATASET,'scorer_version':'workflow-1.0.0','execution_profile':'local-lima',
        'status':'Expansion in progress, reference/control validation pending, no evaluation model exposure',
        'prototype_catalog':original['manifest_id'],'tasks':{},'hashes':{}}
    for key,prior in original['tasks'].items():
        _,_,source=load(ROOT,'workflow-v1',key)
        task=destination/'tasks'/key
        shutil.copytree(source,task)
        identifier=DATASET+'-'+key
        for p in task.rglob('*'):
            if p.is_file() and p.suffix in ('.json','.md','.toml','.sh'):
                p.write_text(p.read_text().replace('workflow-v1-'+key,identifier))
        gold=json.loads((task/'tests/gold.json').read_text())
        gold['hashes']={p.relative_to(task/'tests').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (task/'tests').rglob('*') if p.is_file() and p.name not in ('gold.json','reference.json')}
        write_json(task/'tests/gold.json',gold)
        authoring=json.loads((task/'authoring.json').read_text())
        authoring['prototype_task_sha256']=prior['task_sha256']
        write_json(task/'authoring.json',authoring)
        manifest['tasks'][key]={'task_id':identifier,'path':'datasets/'+DATASET+'/tasks/'+key,'task_sha256':tree_hash(task),
                                'split':'development','source_group':prior['source_group']}
    current=dict(specifications(),**evaluation_specifications())
    for key,spec in current.items():
        group=package(destination,key,spec)
        manifest['tasks'][key]={'task_id':DATASET+'-'+key,'path':'datasets/'+DATASET+'/tasks/'+key,
                               'task_sha256':tree_hash(destination/'tasks'/key),'split':spec.get('split','development'),'source_group':group}
    names=['scripts/build_workflow_suite.py','scripts/workflow_development_cases.py','scripts/workflow_evaluation_cases.py',*original['hashes']]
    for name in names:manifest['hashes'][name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    for name in sorted({spec['source'] for spec in current.values()}):
        for source in (OBSERVATIONS/name).rglob('*'):
            if source.is_file():manifest['hashes'][source.relative_to(ROOT).as_posix()]=hashlib.sha256(source.read_bytes()).hexdigest()
    manifest['scorer_path']=original['scorer_path']
    manifest['scorer_sha256']=original['scorer_sha256']
    manifest['content_hash']=content_hash(manifest)
    manifest['manifest_id']=DATASET+'-canonical-'+manifest['content_hash'][:12]
    write_json(destination/'manifest.json',manifest)
    return manifest


def build(check):
    destination=ROOT/'datasets'/DATASET
    with tempfile.TemporaryDirectory() as directory:
        staged=Path(directory)
        manifest=construct(staged)
        for p in staged.rglob('*'):
            if not p.is_file():continue
            target=destination/p.relative_to(staged)
            if check:
                if not target.is_file() or p.read_bytes()!=target.read_bytes():raise ValueError('workflow_suite_reconstruction_mismatch:'+str(target))
            else:
                if target.exists() and p.read_bytes()!=target.read_bytes():raise ValueError('workflow_suite_preview_already_exists')
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(p.read_bytes())
    print(manifest['manifest_id'],len(manifest['tasks']),'cases')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    build(parser.parse_args().check)
