"""Freeze scoped evidence corrections and explicit financial measurement contracts."""
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
sys.path.insert(0, str(ROOT))
from workpaperbench.catalog import content_hash, load, tree_hash
from review_workflow import seal, write_json

DATASET = 'workflow-v15'
REVIEW = 'config/workflow-contract-adjudication.json'


def construct(destination):
    prior = load(ROOT, 'workflow-v14')
    review = json.loads((ROOT / REVIEW).read_text())
    if review['base_manifest_id'] != prior['manifest_id']:
        raise ValueError('adjudication_base_changed')
    manifest = copy.deepcopy(prior)
    manifest['prior_evidence_revision'] = manifest.pop('evidence_revision')
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
        status='Contract adjudication and public clarification, human/source review pending',
        contract_revision={
            'review_id': review['review_id'],
            'evidence_mappings_reviewed': review['evidence_mappings_reviewed'],
            'evidence_changes': len(review['evidence_patches']),
            'model_visible_changed_tasks': review['model_visible_changed_tasks'],
            'scorer_code_changed': False,
            'numerical_oracle_correction': 'c10 forecast uses independent reported operating-income baseline',
            'saved_output_policy': 'Publicly clarified tasks are diagnostic only, other tasks permit compatible reassessment',
            'human_review': 'pending'})
    for key, old in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v14', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(old['task_id'], identifier))
        gold = json.loads((task / 'tests/gold.json').read_text())
        patches = [r for r in review['evidence_patches'] if r['task'] == key]
        definitions = [r for r in review['public_definition_clarifications'] if r['task'] == key]
        for patch in patches:
            target = gold[patch['group']][patch['output']]
            if {k: target[k] for k in ('evidence', 'context_evidence_allowed')} != patch['original_mapping']:
                raise ValueError('adjudication_mapping_changed')
            target.update(copy.deepcopy(patch['corrected_mapping']))
        contract_path = task / 'environment/output_contract.json'
        contract = json.loads(contract_path.read_text())
        for update in definitions:
            if contract['definitions'][update['output']] != update['before']:
                raise ValueError('adjudication_public_definition_changed')
            contract['definitions'][update['output']] = update['after']
        if definitions:
            write_json(contract_path, contract)
        corrections = [r for r in review['reference_sql_corrections'] if r['task'] == key]
        for correction in corrections:
            name = correction['table']
            sql_path = task / 'solution' / (name + '.sql')
            before = sql_path.read_text()
            if before.count(correction['before']) != 1:
                raise ValueError('adjudication_reference_sql_anchor')
            after = before.replace(correction['before'], correction['after'])
            sql_path.write_text(after)
            solution = task / 'solution/solve.sh'
            script = solution.read_text()
            if before.strip() not in script:
                raise ValueError('adjudication_solution_sql_anchor')
            solution.write_text(script.replace(before.strip(), after.strip()))
            # Only authored reference SQL executes here, never retained candidate SQL.
            with sqlite3.connect((task / 'tests/data.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as connection:
                gold['tables'][name]['rows'] = [list(row) for row in connection.execute(after)]
            for control in gold['controls']:
                with sqlite3.connect((task / 'tests' / control['database']).resolve().as_uri() + '?mode=ro', uri=True) as connection:
                    control['tables'][name] = [list(row) for row in connection.execute(after)]
        author_path = task / 'authoring.json'
        author = json.loads(author_path.read_text())
        author['contract_adjudication'] = {
            'review_id': review['review_id'], 'prior_task_sha256': old['task_sha256'],
            'evidence_changes': [{'group': p['group'], 'output': p['output']} for p in patches],
            'model_visible_clarification': bool(definitions),
            'reference_sql_corrections': [p['table'] for p in corrections],
            'saved_output_compatibility': 'diagnostic_model_visible_change' if definitions else 'compatible_grading_only',
            'human_review': 'pending'}
        write_json(author_path, author)
        seal(task, gold)
        manifest['tasks'][key].update(task_id=identifier,
            path='datasets/' + DATASET + '/tasks/' + key, task_sha256=tree_hash(task))
    for name in (REVIEW, 'scripts/build_workflow_contract_adjudication.py'):
        manifest['hashes'][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    manifest['content_hash'] = content_hash(manifest)
    manifest['manifest_id'] = DATASET + '-canonical-' + manifest['content_hash'][:12]
    write_json(destination / 'manifest.json', manifest)
    return manifest


def build(check):
    with tempfile.TemporaryDirectory() as directory:
        stage = Path(directory)
        manifest = construct(stage)
        expected = {p.relative_to(stage) for p in stage.rglob('*') if p.is_file()}
        output = ROOT / 'datasets' / DATASET
        existing = {p.relative_to(output) for p in output.rglob('*') if p.is_file()}
        if existing - expected:
            raise ValueError('adjudication_catalog_unexpected_files')
        for relative in sorted(expected):
            source, target = stage / relative, output / relative
            if check:
                if not target.is_file() or target.read_bytes() != source.read_bytes():
                    raise ValueError('adjudication_reconstruction_mismatch:' + str(relative))
            else:
                if target.exists() and target.read_bytes() != source.read_bytes():
                    raise ValueError('adjudication_catalog_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
