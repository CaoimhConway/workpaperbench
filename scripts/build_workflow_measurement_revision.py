"""Create a prospective workflow bundle with precise field-level measurement contracts."""
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

DATASET = 'workflow-v13'
REVIEW = 'config/workflow-measurement-review.json'


def construct(destination):
    prior = load(ROOT, 'workflow-v12')
    review = json.loads((ROOT / REVIEW).read_text())
    if review['base_dataset'] != prior['dataset_id']:
        raise ValueError('measurement_review_base_changed')
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
        status='Prospective measurement-contract revision, authored offline only, no candidate runs, human review pending',
        measurement_revision={
            'review_id': review['review_id'],
            'public_definition_addenda': review['definitions'],
            'new_public_definitions': review.get('new_definitions', {}),
            'additional_context_evidence': review['additional_context_evidence'],
            'evidence_decisions': review['evidence_decisions'],
            **review['provenance'],
        })
    for key, old in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v12', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(old['task_id'], identifier))
        contract = json.loads((task / 'environment/output_contract.json').read_text())
        for table, addendum in review['definitions'].get(key, {}).items():
            original = contract['definitions'].get(table)
            if not original:
                raise ValueError('measurement_definition_target_missing:' + key + ':' + table)
            contract['definitions'][table] = original.rstrip() + ' ' + addendum.strip()
        for table, definition in review.get('new_definitions', {}).get(key, {}).items():
            if table in contract['definitions']:
                raise ValueError('measurement_new_definition_already_exists:' + key + ':' + table)
            contract['definitions'][table] = definition.strip()
        write_json(task / 'environment/output_contract.json', contract)
        gold = json.loads((task / 'tests/gold.json').read_text())
        for name, evidence in review['additional_context_evidence'].get(key, {}).items():
            if name in gold['claims']:
                target = gold['claims'][name]['context_evidence_allowed']
            elif name in gold['tables']:
                target = gold['tables'][name]['context_evidence_allowed']
            else:
                raise ValueError('measurement_context_target_missing:' + key + ':' + name)
            target.extend(item for item in evidence if item not in target)
        if review['definitions'].get(key) or review.get('new_definitions', {}).get(key) or review['additional_context_evidence'].get(key):
            authoring = json.loads((task / 'authoring.json').read_text())
            authoring['measurement_revision'] = {
                'prior_task_sha256': old['task_sha256'],
                'public_definition_addenda': review['definitions'].get(key, {}),
                'new_public_definitions': review.get('new_definitions', {}).get(key, {}),
                'additional_context_evidence': review['additional_context_evidence'].get(key, {}),
                'financial_inputs_changed': False,
                'reference_sql_changed': False,
                'human_review': 'pending',
            }
            write_json(task / 'authoring.json', authoring)
        seal(task, gold)
        manifest['tasks'][key].update(task_id=identifier,
            path='datasets/' + DATASET + '/tasks/' + key, task_sha256=tree_hash(task))
    for name in (REVIEW, 'scripts/build_workflow_measurement_revision.py', 'scripts/review_workflow.py'):
        manifest['hashes'][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
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
        existing = {path.relative_to(output) for path in output.rglob('*') if path.is_file()} if output.exists() else set()
        if existing - expected:
            raise ValueError('measurement_catalog_unexpected_files')
        for relative in sorted(expected):
            path, target = stage / relative, output / relative
            if check:
                if not target.is_file() or target.read_bytes() != path.read_bytes():
                    raise ValueError('measurement_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('measurement_catalog_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
