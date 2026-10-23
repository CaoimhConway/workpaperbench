"""Verify experimental task workpapers in the existing isolated verifier, without inference."""
import argparse
import base64
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from workpaperbench.catalog import load
from build_workflow_hard_evaluation import DATASET, digest
from workflow_hard_evaluation_cases import mistakes
from validate_workflow_quality import CONTAINER, VERIFIER_BUILD


def submissions(task,key):
    answer=json.loads((task/'tests/reference.json').read_text())
    sql={t['file']:(task/'solution'/t['file']).read_text() for t in answer['tables']}
    cases=[]
    def add(name, queries=None, payload=None, failure=None, scope='original'):
        files=dict(sql if queries is None else queries)
        files['answer.json']=json.dumps(answer if payload is None else payload)
        cases.append((name,files,failure,scope))
    add('reference')
    add('alternative', {t['file']:(task/'alternative'/t['file']).read_text() for t in answer['tables']})
    reordered={}
    gold=json.loads((task/'tests/gold.json').read_text())
    sufficient=copy.deepcopy(answer)
    for category in ('tables','claims'):
        for entry in sufficient[category]:
            entry['evidence']=gold[category][entry['id']]['evidence'][-1]
    add('alternative_evidence',payload=sufficient)
    context=copy.deepcopy(answer)
    evidence=json.loads((task/'environment/evidence.json').read_text())
    for entry in context['tables']+context['claims']:
        entry['evidence']=[' and '.join(e['id'] for e in evidence)+' - relevant dossier context']
    for t in answer['tables']:
        columns=','.join('"'+n+'"' for n in reversed(gold['tables'][t['id']]['columns']))
        reordered[t['file']]='SELECT '+columns+' FROM ('+sql[t['file']]+') ORDER BY 1 DESC'
    add('reordered_with_context',reordered,context)
    # Optional notes, including feasible witness prose, carry no semantic score.
    notes=copy.deepcopy(answer)
    for entry in notes['claims']: entry['note']='Alternative derivation supplied. No particular witness is required.'
    add('optional_notes',payload=notes)
    for name,mutation in mistakes(key).items():
        changed=dict(sql)
        changed[mutation['table']+'.sql']=mutation['sql']
        add(name,changed,failure=mutation['table'],scope=mutation.get('scope','original'))
    constants={}
    for table,spec in gold['tables'].items():
        constants[table+'.sql']=' UNION ALL '.join('SELECT '+','.join(json.dumps(value)+ ' AS "'+col+'"'
            for col,value in zip(spec['columns'],row)) for row in spec['rows'])
    add('constant_original_answers',constants,failure='all',scope='controls')
    wrong=copy.deepcopy(answer)
    wrong['claims'][0]['verdict']='supported' if wrong['claims'][0]['verdict']!='supported' else 'contradicted'
    add('wrong_claim',payload=wrong,failure='claim')
    missing=copy.deepcopy(answer)
    missing['tables'][0]['evidence']=[]
    add('missing_support',payload=missing,failure='evidence')
    unknown=copy.deepcopy(answer)
    unknown['tables'][0]['evidence'].append(key+':s99')
    add('unknown_evidence',payload=unknown,failure='evidence')
    return cases


def validate_case(verdict,failure,scope):
    assert all(verdict['isolation'].values()),verdict
    assert verdict['checks']['delivery'] is True,verdict
    if failure is None:
        assert verdict['complete'] is True,verdict
    elif failure=='claim':
        assert verdict['checks']['numerical_tables'] and not verdict['checks']['claim_verdicts'],verdict
    elif failure=='evidence':
        assert verdict['checks']['financial_answer'] and not verdict['checks']['evidence'],verdict
    elif scope=='controls':
        assert verdict['checks']['numerical_tables'] and not verdict['checks']['robustness'],verdict
        if failure!='all':
            detail=verdict['details']['tables'][failure]
            assert any(e=='numeric' for e in detail['control_errors'].values()),detail
    else:
        detail=verdict['details']['tables'][failure]
        assert detail['original_error']=='numeric',verdict
        assert verdict['checks']['evidence'] and verdict['checks']['claim_verdicts'],verdict
    assert verdict['complete'] == (failure is None),verdict


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--native-prefix')
    args=parser.parse_args()
    if args.output.exists(): raise ValueError('report_already_exists')
    from guest_bench import preflight
    preflight()
    m=load(ROOT,DATASET)
    report={'dataset':DATASET,'manifest_id':m['manifest_id'],'scorer_sha256':m['scorer_sha256'],
            'validator_sha256':digest(__file__),'inference':False,'external_service_spend_usd':0,
            'scope':'Authored reference, alternative and analytical mutation verification, not model performance',
            'native':[],'cases':[]}
    for key in m['tasks']:
        _,spec,task=load(ROOT,DATASET,key)
        tag='wpb-hard-'+spec['task_sha256'][:16]
        built=subprocess.run([sys.executable,'-c',VERIFIER_BUILD,str(task/'tests'),tag],capture_output=True,text=True)
        if built.returncode: raise RuntimeError(built.stderr)
        for name,files,failure,scope in submissions(task,key):
            payload=json.dumps({n:base64.b64encode(v.encode()).decode() for n,v in files.items()})
            cmd=['docker','run','--rm','--network','none','--read-only','--memory','384m','--cpus','1',
                 '--pids-limit','32','--cap-drop','ALL','--security-opt','no-new-privileges',
                 '--tmpfs','/logs:rw,noexec,nosuid,size=4m','--tmpfs','/tmp:rw,noexec,nosuid,size=4m',
                 '-i',tag,'python','-c',CONTAINER]
            run=subprocess.run(cmd,input=payload,capture_output=True,text=True,check=True,timeout=120)
            verdict=json.loads(run.stdout)
            validate_case(verdict,failure,scope)
            report['cases'].append({'task':key,'variant':name,'expected_failure':failure,'scope':scope,'verdict':verdict})
            print(key,name,'verified',flush=True)
        if args.native_prefix:
            with tempfile.TemporaryDirectory(prefix='wpb-hard-submission-') as temp:
                for name,data in submissions(task,key)[0][1].items(): (Path(temp)/name).write_text(data)
                attempt=args.native_prefix+'-'+key
                subprocess.run([sys.executable,str(ROOT/'scripts/guest_bench.py'),'grade','--dataset',DATASET,
                    '--task',key,'--artifacts',temp,'--attempt',attempt],check=True)
                path=ROOT/'.raw/local-trials'/attempt
                receipt=json.loads((path/'receipt.json').read_text())
                assert receipt['manifest_id']==m['manifest_id'] and not receipt['inference']
                assert receipt['verdict']['complete'] and all(receipt['verdict']['isolation'].values()),receipt
                report['native'].append({'task':key,'receipt_sha256':digest(path/'receipt.json'),
                    'manifest_id':receipt['manifest_id'],'task_sha256':receipt['task_sha256'],
                    'verdict_sha256':digest(path/'verifier.json'),'verdict':receipt['verdict'],
                    'runtime_integrity':receipt.get('runtime_integrity')})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('Verified',len(report['cases']),'isolated cases and',len(report['native']),'native executions')


if __name__=='__main__': main()
