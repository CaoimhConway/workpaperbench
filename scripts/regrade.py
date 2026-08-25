"""Regrade retained submissions in native separate verifiers, without inference."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_OS') != 'Linux':
        raise SystemExit('Replay retained submissions only on the hosted Linux runner')
    if any(k in os.environ for k in ('OPENROUTER_API_KEY','GH_TOKEN','GITHUB_TOKEN')):
        raise SystemExit('No inference or GitHub key belongs in replay')
    manifest=json.loads((ROOT/'config/freeze.json').read_text())
    scorer=hashlib.sha256((ROOT/'workpaperbench/grading.py').read_bytes()+(ROOT/'workpaperbench/sql_worker.py').read_bytes()).hexdigest()
    raw=ROOT/'.raw/regrade'
    raw.mkdir(parents=True,exist_ok=True)
    reviewed=0
    for directory in sorted((ROOT/'reports/runs').iterdir()):
        record_path=directory/'record.json'
        if not record_path.is_file():
            continue
        record=json.loads(record_path.read_text())
        if record.get('campaign')!='final' or record.get('freeze_manifest_id')!=manifest['manifest_id']:
            continue
        submission=directory/'answer.raw.txt'
        if not submission.is_file():
            submission=directory/'answer.json'
        if not submission.is_file():
            continue  # Legacy discarded bytes stay unavailable, never invented.
        content=submission.read_bytes()
        if submission.is_symlink() or len(content)>65536:
            raise ValueError('unsafe_regrade_input')
        name='regrade-'+record['slot_id']
        task=raw/'tasks'/name
        shutil.copytree(ROOT/'tasks'/record['task'],task)
        encoded=base64.b64encode(content).decode()
        script="#!/bin/bash\nset -euo pipefail\npython - <<'WRITE'\nimport base64\nfrom pathlib import Path\nPath('/logs/artifacts/answer.json').write_bytes(base64.b64decode("+repr(encoded)+"))\nWRITE\n"
        (task/'solution/solve.sh').write_text(script)
        command=['harbor','trial','start','-p',str(task),'-a','oracle','--trial-name',name,'--trials-dir',str(raw/'trials')]
        with (raw/(name+'.log')).open('w') as log:
            subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=600,check=True)
        path=raw/'trials'/name/'verifier/verdict.json'
        verdict=json.loads(path.read_text())
        if not all(verdict.get('isolation',{}).get(k) is True for k in ('network_namespace_none','network_probe_blocked','no_inference_key','no_docker_socket')):
            raise ValueError('regrade_isolation_not_established')
        if (record.get('verdict') or {}).get('checks',{}).get('format') is not True and verdict['complete']:
            verdict['complete']=False
            verdict['errors'].append('original_artifact_boundary_unreconstructable')
        review={'manifest_id':manifest['manifest_id'],'scorer_version':verdict['scorer_version'],
                'scorer_sha256':scorer,'input_file':submission.name,
                'input_sha256':hashlib.sha256(content).hexdigest(),'verdict':verdict,
                'run_id':os.environ['GITHUB_RUN_ID'],'commit_sha':os.environ['GITHUB_SHA'],
                'scope':'Same retained answer, pristine inputs, no answer repairs and no model call. Original verdict preserved.'}
        (directory/'regrade.json').write_text(json.dumps(review,indent=2)+'\n')
        reviewed+=1
        print(name,'reviewed')
    print('Reviewed',reviewed,'retained submissions without inference')


if __name__=='__main__':
    main()
