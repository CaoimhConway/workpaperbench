"""Build the frozen four-task financial reasoning evaluation supplement."""
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
from workpaperbench.catalog import content_hash, tree_hash
from workflow_hard_evaluation_cases import specifications, controls, alternatives

DATASET = 'workflow-hard-eval-v1'
BASE = ROOT/'datasets/workflow-v15/tasks/c01'
SOURCES = ROOT/'datasets'/DATASET/'sources'


def write_json(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_data(source):
    return {name:[dict(zip(table['columns'],row)) for row in table['rows']] for name,table in source['tables'].items()}


def database(path, schemas, data):
    with sqlite3.connect(path) as conn:
        for name, rows in data.items():
            columns=schemas[name]['columns']
            conn.execute('CREATE TABLE '+name+' ('+', '.join(k+' '+v for k,v in columns.items())+')')
            conn.executemany('INSERT INTO '+name+' VALUES ('+','.join('?' for _ in columns)+')',
                             [tuple(row[k] for k in columns) for row in rows])


def construct(destination):
    if sqlite3.sqlite_version!='3.45.1':
        raise ValueError('Build with SQLite 3.45.1 on the supported Ubuntu 24.04 controller')
    manifest={'dataset_id':DATASET,'status':'Evaluation supplement frozen before candidate trials, empirical results reported separately',
      'evaluation_track':'construction','scorer_version':'workflow-1.2.1',
      'scorer_path':'config/scorers/workflow-1.2.1.py','sql_worker_path':'config/scorers/workflow_sql_worker-1.2.1.py',
      'starting_commit':'bdaabd3f526b05553efdc0f40af1d5e0576b0142',
      'task_design':'Four source-grounded financial reasoning tasks. Initial package freeze precedes all candidate trials.',
      'human_review':'pending','tasks':{},'hashes':{}}
    for key,s in specifications().items():
        task=destination/'tasks'/key
        for folder in ['environment','tests','solution','alternative']:
            (task/folder).mkdir(parents=True)
        identifier=DATASET+'-'+key
        source=json.loads((SOURCES/(s['source']+'.json')).read_text())
        data=source_data(source)
        evidence=[]
        for entry in source['evidence']:
            evidence.append({'source_url':source['url'],'publication_date':source['publication_date'],
                'source_title':source['title'],'unit':source['unit'],'origin':'authentic_source_facts',
                **entry,'source_extract_sha256':source['extract_sha256']})
        text='# Source dossier\n\n'+source['title']+'\n\n'+source['url']+'\n\n'
        text+='Source date '+source['publication_date']+'. '+source.get('publication_precision','')+' '+source['precision']+'\n\n'
        for e in evidence:
            text+='## '+e['id']+'\n\n'+e['locator']+'\n\n'+e['origin']+'\n\n'
            if e.get('source_url'): text+=e['source_url']+'\n\n'
            text+=e.get('facts','Selected factual table columns are normalized below.')+'\n\n'
        text+='## Normalized input tables\n\nTable origins distinguish source facts from authored scenarios. Full source documents are not redistributed.\n'
        for name,values in data.items():
            text+='\n### '+name+'\n\n'+source['tables'][name].get('origin','authentic_source_facts')+'\n\n```json\n'+json.dumps(values,indent=2)+'\n```\n'
        text+='\n'+source['rights']+'\n'
        database(task/'environment/data.sqlite',source['tables'],data)
        for folder in ['environment','tests']:
            write_json(task/folder/'evidence.json',evidence)
            (task/folder/'sources.md').write_text(text)
            shutil.copyfile(BASE/'environment/schema.json',task/folder/'schema.json')
        shutil.copyfile(task/'environment/data.sqlite',task/'tests/data.sqlite')
        declarations=copy.deepcopy(s['tables'])
        all_evidence=[e['id'] for e in evidence]
        # Every retained extract belongs to the compact relevant dossier. Support
        # sets still require the specific observations needed for each output.
        for declaration in declarations.values():
            declaration['context_evidence_allowed']=all_evidence
        claims=copy.deepcopy(s['claims'])
        for claim in claims.values():
            claim['context_evidence_allowed']=all_evidence
        contract={'tables':{name:{k:v for k,v in t.items() if k not in ['evidence','context_evidence_allowed']} for name,t in declarations.items()},
                  'definitions':s['definitions'],'claim_assertions':{name:c['assertion'] for name,c in claims.items()},
                  'numeric_policy':'Displayed-value arithmetic. Absolute tolerances are computational, not claims of source precision.'}
        if 'assumptions' in s: contract['assumptions']=s['assumptions']
        write_json(task/'environment/output_contract.json',contract)
        (task/'environment/Dockerfile').write_bytes((BASE/'environment/Dockerfile').read_bytes())
        toml=(BASE/'task.toml').read_text().replace('workflow-v15-c01',identifier)
        (task/'task.toml').write_text(toml)
        for name in ['Dockerfile','docker-compose.yaml','verify.py','test.sh']:
            shutil.copyfile(BASE/'tests'/name,task/'tests'/name)
        shutil.copytree(BASE/'tests/workpaperbench',task/'tests/workpaperbench',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        instruction='# '+s['title']+'\n\n'+s['request']+'\n\n'
        instruction+='Read /workspace/sources.md and /workspace/evidence.json. Query /workspace/data.sqlite. The definitions, required columns, row keys, units, precision and assertions are in /workspace/output_contract.json. There is no starting SQL.\n\n'
        instruction+='Deliver exactly /logs/artifacts/answer.json and the three SQL files named '+', '.join(n+'.sql' for n in s['tables'])+'. Each JSON table entry names its SQL file and evidence IDs. Supply each requested table and claim exactly once, with no extra files. Use supported, contradicted or unresolved claim verdicts against the original dossier. The JSON schema is /workspace/schema.json. Optional notes are not semantically graded.\n\n'
        instruction+='SQL must be read-only SELECT/CTE and recompute from the inputs. Controls change relevant observations or authored assumptions consistently, without redefining the financial rules. Claim verdicts are graded on the original dossier only. Equivalent correct derivations and sufficient evidence paths are accepted. Row and column order are ignored. Each query returns at most 100 rows and 16 columns. No file access, writes, extensions or wall-clock dates. JSON is at most 65536 bytes, each SQL file at most 16384 UTF-8 bytes. Use safe lowercase SQL basenames.\n\nTask ID: '+identifier+'\n'
        (task/'instruction.md').write_text(instruction)
        reference={'task_id':identifier,'tables':[{'id':n,'file':n+'.sql','evidence':t['evidence'][0]} for n,t in declarations.items()],
                   'claims':[{'id':n,'verdict':c['verdict'],'evidence':c['evidence'][0]} for n,c in claims.items()]}
        for folder,sqls in [('solution',s['sql']),('alternative',alternatives(key))]:
            for name,sql in sqls.items(): (task/folder/(name+'.sql')).write_text(sql+'\n')
            write_json(task/folder/'answer.json',reference)
        solve='#!/bin/bash\nset -euo pipefail\nmkdir -p /logs/artifacts\n'
        for name,sql in s['sql'].items(): solve+="cat > /logs/artifacts/"+name+".sql <<'SQL'\n"+sql+'\nSQL\n'
        solve+="cat > /logs/artifacts/answer.json <<'ANSWER'\n"+json.dumps(reference,indent=2)+'\nANSWER\n'
        (task/'solution/solve.sh').write_text(solve)
        write_json(task/'tests/reference.json',reference)
        gold={'task_id':identifier,'scorer_version':'workflow-1.2.1','tables':declarations,'claims':claims,'controls':[]}
        for name,values in s['calculate'](data).items(): gold['tables'][name]['rows']=values
        reasons=[]
        for i,(name,rationale,changed) in enumerate(controls(key,data),1):
            file='control-'+str(i)+'.sqlite'
            database(task/'tests'/file,source['tables'],changed)
            gold['controls'].append({'name':name,'database':file,'origin':'authored_synthetic_counterfactual','tables':s['calculate'](changed)})
            reasons.append({'name':name,'rationale':rationale})
        gold['hashes']={p.relative_to(task/'tests').as_posix():digest(p) for p in sorted((task/'tests').rglob('*')) if p.is_file()}
        write_json(task/'tests/gold.json',gold)
        write_json(task/'authoring.json',{'split':'evaluation','evaluation_track':'construction','source_group':s['source'],
            'nearest_existing_counterparts':s['nearest'],'additional_analytical_decisions':s['novelty'],
            'source_snapshot':'datasets/'+DATASET+'/sources/'+s['source']+'.json','source_snapshot_sha256':digest(SOURCES/(s['source']+'.json')),
            'reference_method':'Executable economic model with a separate derivation, valid alternative SQL and financial invariant checks',
            'controls':reasons,'human_review':'pending','source_review':'Primary source headings, definitions and factual values inspected. Independent human review remains pending.',
            'model_exposure':'No candidate trials before initial freeze. Source groups are separate from development tasks. Published references remain a contamination risk.',
            'execution':'Baseline task resources and frozen scorer reused. Qualified GLM uses 3600 seconds and 24 turns. Native Sol uses 3600 seconds and has no equivalent turn cap.'})
        manifest['tasks'][key]={'task_id':identifier,'path':'datasets/'+DATASET+'/tasks/'+key,'task_sha256':tree_hash(task),
            'split':'evaluation','source_group':s['source'],'evaluation_track':'construction'}
    bound=['scripts/build_workflow_hard_evaluation.py','scripts/workflow_hard_evaluation_cases.py',
           'scripts/workflow_hard_borrowing_base.py','scripts/workflow_hard_acquisition.py',
           'scripts/workflow_hard_receivables.py','scripts/workflow_hard_waterfall.py',
           'scripts/validate_workflow_hard_evaluation.py','tests/test_workflow_hard_evaluation.py',
           'tests/test_hard_borrowing_base.py','tests/test_hard_acquisition.py',
           'tests/test_hard_receivables.py','tests/test_hard_waterfall.py',manifest['scorer_path'],manifest['sql_worker_path']]
    bound += [p.relative_to(ROOT).as_posix() for p in sorted(SOURCES.glob('*.json'))]
    bound += [p.relative_to(ROOT).as_posix() for p in sorted((SOURCES.parent/'references').glob('*.md'))]
    for name in bound: manifest['hashes'][name]=digest(ROOT/name)
    manifest['scorer_sha256']=manifest['hashes'][manifest['scorer_path']]
    manifest['sql_worker_sha256']=manifest['hashes'][manifest['sql_worker_path']]
    manifest['content_hash']=content_hash(manifest)
    manifest['manifest_id']=DATASET+'-canonical-'+manifest['content_hash'][:12]
    write_json(destination/'manifest.json',manifest)
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    target=ROOT/'datasets'/DATASET
    with tempfile.TemporaryDirectory(prefix='wpb-hard-build-') as temporary:
        staged=Path(temporary)
        m=construct(staged)
        if args.check:
            assert tree_hash(staged/'tasks')==tree_hash(target/'tasks'), 'task_bytes_changed'
            assert (staged/'manifest.json').read_bytes()==(target/'manifest.json').read_bytes(), 'manifest_changed'
        else:
            if (target/'tasks').exists(): raise ValueError('refuse_overwrite_existing_tasks')
            shutil.copytree(staged/'tasks',target/'tasks')
            shutil.copyfile(staged/'manifest.json',target/'manifest.json')
    print(m['manifest_id'])


if __name__=='__main__': main()
