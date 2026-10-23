"""Freeze source-backed evidence mappings without changing the public workpapers."""
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

DATASET = 'workflow-v14'
REVIEW = 'config/workflow-evidence-review.json'


def construct(destination):
    prior = load(ROOT, 'workflow-v13')
    review = json.loads((ROOT / REVIEW).read_text())
    if review['base_manifest_id'] != prior['manifest_id']:
        raise ValueError('evidence_review_base_changed')
    records = {(row['task'], row['group'], row['output']): row
               for row in review['mappings']}
    if len(records) != len(review['mappings']):
        raise ValueError('evidence_review_duplicate_mapping')
    covered = set()
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
        status='Grading-only evidence revision, independent human and source review pending',
        evidence_revision={
            'review_id': review['review_id'], 'mapping_count': len(records),
            'changed_mappings': [list(key) for key, row in records.items() if row['changed']],
            'model_visible_changes_except_identity': False,
            'financial_targets_changed': False, 'reference_sql_changed': False,
            'scorer_changed': False, 'human_review': 'pending',
        })
    for key, old in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v13', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(old['task_id'], identifier))
        gold = json.loads((task / 'tests/gold.json').read_text())
        changes = []
        for group in ('tables', 'claims'):
            for name, spec in gold[group].items():
                target = (key, group, name)
                covered.add(target)
                row = records[target]
                before = {field: spec[field] for field in ('evidence', 'context_evidence_allowed')}
                if row['original_mapping'] != before:
                    raise ValueError('evidence_review_mapping_changed:' + ':'.join(target))
                after = row['corrected_mapping']
                if set(after) != set(before) or row['changed'] != (before != after):
                    raise ValueError('evidence_review_patch_shape:' + ':'.join(target))
                known = {item['id'] for item in json.loads((task / 'environment/evidence.json').read_text())}
                if (not after['evidence'] or any(not option for option in after['evidence'])
                        or any(source_id not in known for option in after['evidence'] for source_id in option)
                        or any(source_id not in known for source_id in after['context_evidence_allowed'])):
                    raise ValueError('evidence_review_unknown_or_empty_source:' + ':'.join(target))
                spec.update(copy.deepcopy(after))
                if row['changed']:
                    changes.append({'group': group, 'output': name,
                                    'before': before, 'after': after})
        reference_path = task / 'tests/reference.json'
        original_reference = reference_path.read_text().strip()
        reference = json.loads(original_reference)
        reference_changes = review.get('authored_reference_updates', {}).get(key, {})
        for group, outputs in reference_changes.items():
            for name, citations in outputs.items():
                entry = next(item for item in reference[group] if item['id'] == name)
                entry['evidence'] = citations
        if reference_changes:
            write_json(reference_path, reference)
            path = task / 'solution/solve.sh'
            script = path.read_text()
            if script.count(original_reference) != 1:
                raise ValueError('evidence_reference_answer_anchor:' + key)
            path.write_text(script.replace(original_reference, reference_path.read_text().strip()))
        if changes:
            path = task / 'authoring.json'
            authoring = json.loads(path.read_text())
            authoring['evidence_revision'] = {
                'review_id': review['review_id'], 'prior_task_sha256': old['task_sha256'],
                'changes': changes, 'grading_only': True,
                'authored_reference_citations': reference_changes,
                'public_requirements_changed': False, 'human_review': 'pending',
            }
            write_json(path, authoring)
        seal(task, gold)
        manifest['tasks'][key].update(task_id=identifier,
            path='datasets/' + DATASET + '/tasks/' + key, task_sha256=tree_hash(task))
    if covered != set(records):
        raise ValueError('evidence_review_coverage')
    for name in (REVIEW, 'scripts/build_workflow_evidence_revision.py'):
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
        existing = {path.relative_to(output) for path in output.rglob('*') if path.is_file()}
        if existing - expected:
            raise ValueError('evidence_catalog_unexpected_files')
        for relative in sorted(expected):
            path, target = stage / relative, output / relative
            if check:
                if not target.is_file() or target.read_bytes() != path.read_bytes():
                    raise ValueError('evidence_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('evidence_catalog_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
