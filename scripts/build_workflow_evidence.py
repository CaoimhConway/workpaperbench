"""Correct source-support bindings without changing financial workflow tasks."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workpaperbench.catalog import content_hash, load, tree_hash

DATASET = 'workflow-v4'


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def construct(destination):
    prior = load(ROOT, 'workflow-v3')
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
                    status='Corrected evidence bindings, financial requirements unchanged',
                    grading_correction={'number': 1, 'component': 'evidence',
                        'reason': 'Pair both SBC economic dates and both signature dates with their actual locators. Accept additional known dossier context with sufficient reviewed support.'})
    for key, original in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v3', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(original['task_id'], identifier))
        path = task / 'tests/gold.json'
        gold = json.loads(path.read_text())
        evidence = json.loads((task / 'environment/evidence.json').read_text())
        gold['context_evidence_allowed'] = [entry['id'] for entry in evidence]
        if key == 'b01':
            amounts = [['b01:s01', 'b01:s04']]
            dates = [['b01:s03', 'b01:s06'], ['b01:s01', 'b01:s04'],
                     ['b01:s01', 'b01:s06'], ['b01:s03', 'b01:s04']]
            for name in ('reserve_coverage', 'reserve_bridge'):
                gold['tables'][name]['evidence'] = amounts
            gold['tables']['signature_lag']['evidence'] = dates
            gold['claims']['base_coverage_sql_is_valid']['evidence'] = amounts
            gold['claims']['signature_lag_sql_is_valid']['evidence'] = dates
            gold['claims']['observations_identify_payments_volume']['evidence'] = [
                ['b01:s02'], ['b01:s05'], ['b01:s01', 'b01:s04']]
            reference = json.loads((task / 'tests/reference.json').read_text())
            for role in ('tables', 'claims'):
                for entry in reference[role]:
                    entry['evidence'] = gold[role][entry['id']]['evidence'][0]
            write_json(task / 'tests/reference.json', reference)
            script = (task / 'solution/solve.sh').read_text()
            script = script.split("cat > /logs/artifacts/answer.json <<'ANSWER'", 1)[0]
            script += "cat > /logs/artifacts/answer.json <<'ANSWER'\n" + json.dumps(reference, indent=2) + '\nANSWER\n'
            (task / 'solution/solve.sh').write_text(script)
        gold['hashes'] = {name: hashlib.sha256((task / 'tests' / name).read_bytes()).hexdigest()
                          for name in gold['hashes']}
        write_json(path, gold)
        path = task / 'authoring.json'
        authoring = json.loads(path.read_text())
        authoring['grading_correction'] = {'number': 1, 'prior_task_sha256': original['task_sha256'],
            'changes': 'Correct SBC source bindings and accept known dossier context with sufficient support. No financial, source, SQL or counterfactual changes.'}
        write_json(path, authoring)
        manifest['tasks'][key].update(task_id=identifier, path='datasets/' + DATASET + '/tasks/' + key,
                                     task_sha256=tree_hash(task))
    manifest['hashes']['scripts/build_workflow_evidence.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest['content_hash'] = content_hash(manifest)
    manifest['manifest_id'] = DATASET + '-canonical-' + manifest['content_hash'][:12]
    write_json(destination / 'manifest.json', manifest)
    return manifest


def build(check):
    with tempfile.TemporaryDirectory() as directory:
        staged = Path(directory)
        manifest = construct(staged)
        for path in staged.rglob('*'):
            if not path.is_file():
                continue
            target = ROOT / 'datasets' / DATASET / path.relative_to(staged)
            if check:
                if not target.is_file() or target.read_bytes() != path.read_bytes():
                    raise ValueError('workflow_evidence_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('workflow_evidence_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
