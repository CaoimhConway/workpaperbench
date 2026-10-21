"""Freeze explicit calculation conventions and tolerance-preserving row keys."""
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

DATASET = 'workflow-v10'
SCORER_VERSION = 'workflow-1.2.1'
SCORER = 'config/scorers/workflow-1.2.1.py'
WORKER = 'config/scorers/workflow_sql_worker-1.2.1.py'
REVISIONS = {
    'c01': {
        'reconciliation_keys': [],
        'reason': 'The reconciliation is a singleton table. Measurements retain their numerical tolerances instead of serving as exact row identifiers.',
    },
    'b02': {
        'stock_bridge_definition': 'Use January 30 to February 10 and February 10 to February 27. Each stock is the reported observation in reserve_observations. Treasury change uses treasury_fair_value_usd, asset change uses reported_assets_usd, and cash, repo and token changes use cash_usd, repo_fair_value_usd and redeemable_tokens. Changes are current less prior stocks, with surplus change equal to asset change less redeemable-token change. This reported-stock basis is separate from the holdings-based reconstruction in qualified_coverage and treasury_valuation. Preserve any difference between reported and reconstructed values.',
    },
    'b06': {
        'corporate_bridge_definition': 'For each year, segment_sum_usd_million is summed segment adjusted EBITDA. total_adjusted_ebitda_usd_million is reconstructed as that sum plus the signed corporate_cost_usd_million. The EBITDA residual is reconstructed total adjusted EBITDA less platform.adjusted_ebitda_usd_million. The bookings residual is summed segment bookings less platform.bookings_usd_million, and the revenue residual is summed segment revenue less platform.revenue_usd_million. total_ebitda_to_bookings_pct is 100 times reconstructed total adjusted EBITDA divided by summed segment bookings. Reported platform totals remain independent reconciliation observations even when they disagree with reconstructed totals.',
        'additional_claim_1_evidence': ['b06:s01'],
        'evidence_reason': 'The supplied segment comparison source explicitly describes revenue divided by bookings as a descriptive accounting ratio, not a uniquely identified commission.',
    },
}
REVISION = {
    'tasks': REVISIONS,
    'financial_inputs_changed': False,
    'financial_targets_changed': False,
    'controls_changed': False,
    'reference_sql_changed': False,
    'scorer_changed': True,
    'sql_transport_changed': True,
    'new_inference': False,
}


def construct(destination):
    prior = load(ROOT, 'workflow-v9')
    scorer_hash = hashlib.sha256((ROOT / SCORER).read_bytes()).hexdigest()
    worker_hash = hashlib.sha256((ROOT / WORKER).read_bytes()).hexdigest()
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
        scorer_version=SCORER_VERSION, scorer_path=SCORER, scorer_sha256=scorer_hash,
        sql_worker_path=WORKER, sql_worker_sha256=worker_hash,
        status='Software and authored controls only, no candidate runs on revised tasks',
        contract_revision=REVISION)
    for key, old in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v9', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(old['task_id'], identifier))
        gold = json.loads((task / 'tests/gold.json').read_text())
        if gold['scorer_version'] != prior['scorer_version']:
            raise ValueError('contract_scorer_base_changed:' + key)
        gold['scorer_version'] = SCORER_VERSION
        contract_path = task / 'environment/output_contract.json'
        contract = json.loads(contract_path.read_text())
        if key == 'c01':
            if (gold['tables']['reconciliation']['keys'] != ['revenue_change_usd_thousand']
                    or contract['tables']['reconciliation']['keys'] != ['revenue_change_usd_thousand']):
                raise ValueError('contract_reconciliation_key_base_changed')
            gold['tables']['reconciliation']['keys'] = []
            contract['tables']['reconciliation']['keys'] = []
        elif key == 'b02':
            expected = 'Use January 30 to February 10 and February 10 to February 27. Changes are current less prior stocks, with surplus change equal to asset change less redeemable-token change.'
            if contract['definitions']['stock_bridge'] != expected:
                raise ValueError('contract_stock_bridge_base_changed')
            contract['definitions']['stock_bridge'] = REVISIONS[key]['stock_bridge_definition']
        elif key == 'b06':
            expected = 'Signed corporate costs plus segment EBITDA equals total EBITDA. Retain booking and revenue reconciliation residuals.'
            if contract['definitions']['corporate_bridge'] != expected:
                raise ValueError('contract_corporate_bridge_base_changed')
            if gold['claims']['claim_1']['evidence'] != [['b06:s01', 'b06:s03']]:
                raise ValueError('contract_commission_evidence_base_changed')
            contract['definitions']['corporate_bridge'] = REVISIONS[key]['corporate_bridge_definition']
            gold['claims']['claim_1']['evidence'].append(REVISIONS[key]['additional_claim_1_evidence'])
        if key in REVISIONS:
            write_json(contract_path, contract)
        shutil.copyfile(ROOT / SCORER, task / 'tests/workpaperbench/workflow_grading.py')
        shutil.copyfile(ROOT / WORKER, task / 'tests/workpaperbench/workflow_sql_worker.py')
        authoring_path = task / 'authoring.json'
        authoring = json.loads(authoring_path.read_text())
        authoring['contract_correction'] = {
            'prior_task_sha256': old['task_sha256'],
            'scorer_version': SCORER_VERSION,
            'scorer_sha256': scorer_hash,
            'sql_worker_sha256': worker_hash,
            'changes': REVISIONS.get(key, {}),
            'financial_inputs_changed': False,
            'financial_targets_changed': False,
            'controls_changed': False,
            'reference_sql_changed': False,
            'new_inference': False,
        }
        write_json(authoring_path, authoring)
        seal(task, gold)
        manifest['tasks'][key].update(task_id=identifier,
            path='datasets/' + DATASET + '/tasks/' + key, task_sha256=tree_hash(task))
    for name in (SCORER, WORKER, 'scripts/build_workflow_contract_revision.py'):
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
            raise ValueError('contract_catalog_unexpected_files')
        for relative in sorted(expected):
            path, target = stage / relative, output / relative
            if check:
                if not target.is_file() or target.read_bytes() != path.read_bytes():
                    raise ValueError('contract_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('contract_catalog_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'construction cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
