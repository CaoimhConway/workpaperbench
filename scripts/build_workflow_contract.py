"""Publish the existing workflow suite with an explicit filesystem contract."""
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

DATASET = 'workflow-v3'
FILE_PATTERN = r'^[a-z][a-z0-9_]{0,40}\.sql$(?!\n)'


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def construct(destination):
    prior = load(ROOT, 'workflow-v2')
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
                    status='Explicit artifact contract, quality evidence reported separately',
                    contract_revision={'number': 1, 'reason': 'Disclose the existing SQL basename rule, artifact directory and input database path'})
    for key, original in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v2', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(original['task_id'], identifier))
        for folder in ('environment', 'tests'):
            path = task / folder / 'schema.json'
            schema = json.loads(path.read_text())
            schema['properties']['tables']['items']['properties']['file'].update(
                pattern=FILE_PATTERN,
                description='SQL basename in /logs/artifacts, beginning with a lowercase letter, followed by at most 40 lowercase letters, digits or underscores, then .sql. No directory or whitespace.')
            write_json(path, schema)
        path = task / 'instruction.md'
        instruction = path.read_text().replace(
            'The SQLite tables contain source-derived observations.',
            'The input database is /workspace/data.sqlite. Its SQLite tables contain source-derived observations.')
        instruction = instruction.replace(
            'Deliver /logs/artifacts/answer.json and one read-only SELECT/CTE .sql file per requested named table.',
            'Deliver /logs/artifacts/answer.json and one read-only SELECT/CTE .sql file per requested named table, all in /logs/artifacts. In each JSON table entry, file is the SQL basename, for example reserve_bridge.sql, relative to answer.json. Absolute paths and directory prefixes are rejected. SQL basenames begin with a lowercase letter, followed by at most 40 lowercase letters, digits or underscores, then .sql. Create regular files without symlinks. Include each requested table and claim ID exactly once.')
        path.write_text(instruction)
        path = task / 'environment/output_contract.json'
        public = json.loads(path.read_text())
        public['filesystem'] = {'input_database': '/workspace/data.sqlite',
                                'answer_file': '/logs/artifacts/answer.json',
                                'sql_directory': '/logs/artifacts',
                                'json_file_fields': 'SQL basenames relative to answer.json'}
        write_json(path, public)
        path = task / 'tests/gold.json'
        gold = json.loads(path.read_text())
        gold['hashes'] = {name: hashlib.sha256((task / 'tests' / name).read_bytes()).hexdigest()
                          for name in gold['hashes']}
        write_json(path, gold)
        path = task / 'authoring.json'
        authoring = json.loads(path.read_text())
        authoring['contract_revision'] = {'number': 1, 'prior_task_sha256': original['task_sha256'],
                                         'changes': 'Explicit input database, output directory and existing basename restriction'}
        write_json(path, authoring)
        manifest['tasks'][key].update(task_id=identifier, path='datasets/' + DATASET + '/tasks/' + key,
                                     task_sha256=tree_hash(task))
    manifest['hashes']['scripts/build_workflow_contract.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
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
                    raise ValueError('workflow_contract_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('workflow_contract_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
