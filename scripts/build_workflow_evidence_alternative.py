"""Freeze a sufficient alternative Microsoft citation without changing calculations."""
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

DATASET = 'workflow-v7'
REVISION = {
    'component': 'evidence',
    'task': 'a01',
    'outputs': ['quarter_model', 'quarter_reconciliation', 'claim_1'],
    'additional_sufficient_evidence': ['a03:s05'],
    'reason': 'The segment table includes matching consolidated revenue and operating-income totals for both three- and six-month periods in both fiscal years.',
    'source': 'https://www.microsoft.com/en-us/Investor/earnings/FY-2025-Q2/press-release-webcast',
    'locator': 'Segment Revenue and Operating Income, Total rows, three and six months ended December 31, 2024 and 2023',
    'new_inference': False,
    'financial_inputs_changed': False,
    'claims_changed': False,
    'scorer_changed': False,
}


def construct(destination):
    prior = load(ROOT, 'workflow-v6')
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
                    status='Software and authored controls only, no candidate runs on revised tasks',
                    evidence_alternative_revision=REVISION)
    for key, old in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v6', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(old['task_id'], identifier))
        gold = json.loads((task / 'tests/gold.json').read_text())
        if key == 'a01':
            for group, names in [('tables', ['quarter_model', 'quarter_reconciliation']),
                                 ('claims', ['claim_1'])]:
                for name in names:
                    if gold[group][name]['evidence'] != [['a03:s02', 'a03:s03']]:
                        raise ValueError('alternative_evidence_base_changed:' + name)
                    gold[group][name]['evidence'].append(['a03:s05'])
            authoring = json.loads((task / 'authoring.json').read_text())
            authoring['evidence_alternative_revision'] = {
                'prior_task_sha256': old['task_sha256'], **REVISION}
            write_json(task / 'authoring.json', authoring)
        seal(task, gold)
        manifest['tasks'][key].update(task_id=identifier,
            path='datasets/' + DATASET + '/tasks/' + key, task_sha256=tree_hash(task))
    manifest['hashes']['scripts/build_workflow_evidence_alternative.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest['content_hash'] = content_hash(manifest)
    manifest['manifest_id'] = DATASET + '-canonical-' + manifest['content_hash'][:12]
    write_json(destination / 'manifest.json', manifest)
    return manifest


def build(check):
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp)
        manifest = construct(stage)
        for path in stage.rglob('*'):
            if not path.is_file():
                continue
            target = ROOT / 'datasets' / DATASET / path.relative_to(stage)
            if check:
                if not target.is_file() or target.read_bytes() != path.read_bytes():
                    raise ValueError('evidence_alternative_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('evidence_alternative_catalog_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
