"""Freeze independent cost, activity, volume and margin controls."""
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

DATASET = 'workflow-v11'
CONTROLS = {
    'c01': {
        'name': 'subscription_cost_increases_with_matching_total',
        'changes': [
            ['costs', {'period_end': '2024-12-31', 'months': 12,
                       'category': 'Subscription and services-based costs'}, 'amount', 1000],
            ['costs', {'period_end': '2024-12-31', 'months': 12,
                       'category': 'Total cost of revenue'}, 'amount', 1000]],
        'reason': 'Subscription cost varies independently of revenue. Matching reported total cost preserves the original reconciliation residuals and reduces current subscription and aggregate gross profit by USD 1 million.',
    },
    'b06': {
        'name': 'trips_increase_with_consumers_fixed',
        'changes': [['platform', {'year': 2025}, 'trips_million', 202]],
        'reason': 'Quarterly trips vary independently of monthly consumers. FY2025 consumers remain 202 million and the period remains three months. Both activity ratios must be recomputed.',
    },
    'b03': {
        'name': 'consumer_spot_volume_increases_with_revenue_fixed',
        'changes': [['spot_volume', {'period': 'Q4FY2025', 'segment': 'consumer'},
                     'volume_usd_billion', 10]],
        'reason': 'Consumer spot volume varies independently of booked revenue. The apparent revenue-to-spot ratio changes without identifying a commission or changing annual revenue attribution or USDC economics.',
    },
    'c04': {
        'name': 'operating_costs_increase_with_revenue_fixed',
        'changes': [
            ['financials', {'period': 'Q4FY2025'}, 'gaap_expense_usd_million', 100],
            ['financials', {'period': 'Q4FY2025'}, 'adjusted_expense_usd_million', 100],
            ['financials', {'period': 'FY2025'}, 'gaap_expense_usd_million', 100],
            ['financials', {'period': 'FY2025'}, 'adjusted_expense_usd_million', 100]],
        'reason': 'An additional USD 100 million Q4 operating expense also enters the annual period, on both reporting bases. Revenue and excluded items remain fixed. Margins and operating income change while existing rounded disclosure residuals are preserved.',
    },
}


def add_control(task, gold, definition):
    filename = 'control-independent.sqlite'
    shutil.copyfile(task / 'tests/data.sqlite', task / 'tests' / filename)
    with sqlite3.connect(task / 'tests' / filename) as db:
        for table, selector, column, delta in definition['changes']:
            where = ' AND '.join(name + '=?' for name in selector)
            result = db.execute('UPDATE ' + table + ' SET ' + column + '=' + column +
                                '+? WHERE ' + where, [delta, *selector.values()])
            if result.rowcount != 1:
                raise ValueError('dependency_control_selector_changed')
        tables = {name: [list(row) for row in db.execute(
            (task / 'solution' / (name + '.sql')).read_text()).fetchall()]
            for name in gold['tables']}
    gold['controls'].append({**definition, 'database': filename,
        'origin': 'authored_synthetic_counterfactual', 'tables': tables})


def construct(destination):
    prior = load(ROOT, 'workflow-v10')
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
        status='Software and authored controls only, no candidate runs on revised tasks',
        dependency_revision={'controls': CONTROLS, 'original_observations_changed': False,
            'original_targets_changed': False, 'reference_sql_changed': False,
            'scorer_changed': False, 'new_inference': False})
    for key, old in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v10', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(old['task_id'], identifier))
        gold = json.loads((task / 'tests/gold.json').read_text())
        if key in CONTROLS:
            add_control(task, gold, CONTROLS[key])
            authoring = json.loads((task / 'authoring.json').read_text())
            authoring['dependency_revision'] = {
                'prior_task_sha256': old['task_sha256'], **CONTROLS[key],
                'original_observations_changed': False, 'original_targets_changed': False,
                'human_review': 'pending'}
            write_json(task / 'authoring.json', authoring)
        seal(task, gold)
        manifest['tasks'][key].update(task_id=identifier,
            path='datasets/' + DATASET + '/tasks/' + key, task_sha256=tree_hash(task))
    manifest['hashes']['scripts/build_workflow_dependency_revision.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
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
            raise ValueError('dependency_catalog_unexpected_files')
        for relative in sorted(expected):
            path, target = stage / relative, output / relative
            if check:
                if not target.is_file() or target.read_bytes() != path.read_bytes():
                    raise ValueError('dependency_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('dependency_catalog_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'construction cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
