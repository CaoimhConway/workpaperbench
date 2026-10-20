"""Freeze sufficient PYUSD claim support and an explicit residual direction."""
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
from review_workflow import seal, write_json

DATASET = 'workflow-v9'
REVISION = {
    'task': 'b02',
    'additional_claim_3_evidence': ['b02:s01', 'b02:s02'],
    'evidence_reason': 'The January and February asset comparisons support assets exceeding tokens at the requested original observation dates. The detailed Treasury schedule is not necessary for this standalone claim.',
    'treasury_residual_definition': 'Residual is deduplicated Treasury-holding fair value less the reported Treasury asset-category fair value at the same economic date.',
    'financial_inputs_changed': False,
    'financial_targets_changed': False,
    'controls_changed': False,
    'scorer_changed': False,
    'new_inference': False,
}


def construct(destination):
    prior = load(ROOT, 'workflow-v8')
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
        status='Software and authored controls only, no candidate runs on revised tasks',
        pyusd_revision=REVISION)
    for key, old in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v8', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(old['task_id'], identifier))
        gold = json.loads((task / 'tests/gold.json').read_text())
        if key == 'b02':
            if gold['claims']['claim_3']['evidence'] != [['b02:s01', 'b02:s02', 'b02:s05']]:
                raise ValueError('pyusd_evidence_base_changed')
            gold['claims']['claim_3']['evidence'].append(REVISION['additional_claim_3_evidence'])
            contract_path = task / 'environment/output_contract.json'
            contract = json.loads(contract_path.read_text())
            if 'Residual' in contract['definitions']['treasury_valuation']:
                raise ValueError('pyusd_residual_base_changed')
            contract['definitions']['treasury_valuation'] += ' ' + REVISION['treasury_residual_definition']
            write_json(contract_path, contract)
            authoring = json.loads((task / 'authoring.json').read_text())
            authoring['pyusd_revision'] = {'prior_task_sha256': old['task_sha256'], **REVISION}
            write_json(task / 'authoring.json', authoring)
        seal(task, gold)
        manifest['tasks'][key].update(task_id=identifier,
            path='datasets/' + DATASET + '/tasks/' + key, task_sha256=tree_hash(task))
    manifest['hashes']['scripts/build_workflow_pyusd_revision.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest['content_hash'] = content_hash(manifest)
    manifest['manifest_id'] = DATASET + '-canonical-' + manifest['content_hash'][:12]
    write_json(destination / 'manifest.json', manifest)
    return manifest


def build(check):
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp)
        manifest = construct(stage)
        expected = {path.relative_to(stage) for path in stage.rglob('*') if path.is_file()}
        output = ROOT / 'datasets' / DATASET
        existing = {path.relative_to(output) for path in output.rglob('*') if path.is_file()}
        if existing - expected:
            raise ValueError('pyusd_catalog_unexpected_files')
        for relative in sorted(expected):
            path, target = stage / relative, output / relative
            if check:
                if not target.is_file() or target.read_bytes() != path.read_bytes():
                    raise ValueError('pyusd_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('pyusd_catalog_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'construction cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
