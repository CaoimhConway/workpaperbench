"""Freeze sufficient evidence alternatives and explicit reconciliation bases."""
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

DATASET = 'workflow-v12'
SQLITE_VERSION = '3.45.1'
ALTERNATIVES = {
    'a02': {'claim_1': [['a02:s03']]},
    'a04': {'claim_1': [['a04:s02']], 'claim_3': [['a04:s03']]},
    'a10': {'claim_2': [['a10:s02']]},
    'b09': {'claim_1': [['b09:s03']]},
    'b10': {'claim_3': [['b10:s01'], ['b10:s02']]},
    'c04': {'claim_2': [['c04:s03']]},
    'c10': {'claim_1': [['c10:s02']]},
}
DEFINITIONS = {
    'b01': {
        'reserve_bridge': 'Changes are June less May stocks, not transaction flows. Reserve change is (June cash + June government debt) minus (May cash + May government debt). Use these component sums for the coverage change as well. Keep reported reserve fair values independent, with component sums less reported fair values as the reserve_coverage residuals. Signature lags are calendar days, not known publication delays.'},
    'b10': {
        'parent_earnings_bridge': 'After-tax parent scope for three years. Parent income is the sum of the disclosed after-tax parent earnings components. Operating earnings remove signed investment gains and signed equity-method impairments from that sum. Residual is the component sum less independently reported parent income.',
        'consolidated_cash_bridge': 'Consolidated scope for three years. Parent income retains the independently reported parent amount, rather than the component sum in parent_earnings_bridge. Add all signed statement adjustments to consolidated net earnings. Noncontrolling income is consolidated less reported parent income.'},
    'c02': {
        'operating_reconciliation': 'Include FY2024, FY2025, Q4FY2024, Q3FY2025 and Q4FY2025. The adjusted_operating_income_usd_million column retains independently reported non-GAAP operating income. Adjustments sum the signed adjustment rows. Residual is GAAP plus those adjustments less reported non-GAAP operating income.'},
    'c03': {
        'net_income_reconciliation': 'Use the net-income column of each reconciliation, already after tax. Adjusted income is reconstructed as GAAP income plus the signed after-tax adjustment rows. Residual is that reconstructed amount less independently reported adjusted income. Missing categories are not separately observed adjustments.',
        'income_growth_bridge': 'Windows FY and Q4FY compare FY2025 with FY2024. Use independently reported GAAP and adjusted income for both periods, rather than the reconstructed adjusted amount in net_income_reconciliation. Gap change is current reported adjusted-minus-GAAP gap less prior reported gap.'},
}
CONTROL = {
    'name': 'reported_reserve_changes_with_components_fixed',
    'changes': [['reserve_reports', {'report_date': '2025-05-31'}, 'reported_reserve_fv_usd', 19]],
    'reason': 'Reported reserve fair value varies independently of cash and government debt. The component-based bridge and coverage stay fixed, while component reserves less reported fair value changes.'}


def add_reported_control(task, gold):
    filename = 'control-reported-reserve.sqlite'
    shutil.copyfile(task / 'tests/data.sqlite', task / 'tests' / filename)
    with sqlite3.connect(task / 'tests' / filename) as db:
        result = db.execute('UPDATE reserve_reports SET reported_reserve_fv_usd=reported_reserve_fv_usd+? WHERE report_date=?', (19, '2025-05-31'))
        if result.rowcount != 1:
            raise ValueError('reported_reserve_control_selector_changed')
        tables = {name: [list(row) for row in db.execute(
            (task / 'solution' / (name + '.sql')).read_text()).fetchall()]
            for name in gold['tables']}
    gold['controls'].append({**CONTROL, 'database': filename,
        'origin': 'authored_synthetic_counterfactual', 'tables': tables})


def construct(destination):
    if sqlite3.sqlite_version != SQLITE_VERSION:
        raise ValueError('grading_contract_builder_requires_sqlite_' + SQLITE_VERSION)
    prior = load(ROOT, 'workflow-v11')
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
        status='Software and authored controls only, no candidate runs on revised tasks',
        grading_contract_revision={'evidence_alternatives': ALTERNATIVES,
            'public_definitions': DEFINITIONS, 'reported_reserve_control': CONTROL,
            'builder_sqlite_version': SQLITE_VERSION,
            'original_observations_changed': False, 'original_targets_changed': False,
            'reference_sql_changed': False, 'scorer_changed': False, 'new_inference': False})
    for key, old in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v11', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(old['task_id'], identifier))
        gold = json.loads((task / 'tests/gold.json').read_text())
        for name, options in ALTERNATIVES.get(key, {}).items():
            gold['claims'][name]['evidence'].extend(options)
        if key in DEFINITIONS:
            contract = json.loads((task / 'environment/output_contract.json').read_text())
            contract['definitions'].update(DEFINITIONS[key])
            write_json(task / 'environment/output_contract.json', contract)
        if key == 'b01':
            path = task / 'instruction.md'
            text = path.read_text()
            anchor = 'Read the source headings'
            text = text.replace(anchor, 'Reserve change is (June cash + June government debt) minus (May cash + May government debt). Preserve independently reported reserve fair values and the component-minus-reported reconciliation residual.\n\n' + anchor, 1)
            path.write_text(text)
            for name in ('reserve_coverage', 'reserve_bridge'):
                gold['tables'][name]['context_evidence_allowed'].extend(['b01:s03', 'b01:s06'])
            add_reported_control(task, gold)
        if key in ALTERNATIVES or key in DEFINITIONS:
            authoring = json.loads((task / 'authoring.json').read_text())
            authoring['grading_contract_revision'] = {
                'prior_task_sha256': old['task_sha256'],
                'additional_sufficient_evidence': ALTERNATIVES.get(key, {}),
                'public_definitions': DEFINITIONS.get(key, {}),
                'observation_date_context_added': key == 'b01',
                'original_observations_changed': False, 'original_targets_changed': False,
                'human_review': 'pending'}
            write_json(task / 'authoring.json', authoring)
        seal(task, gold)
        manifest['tasks'][key].update(task_id=identifier,
            path='datasets/' + DATASET + '/tasks/' + key, task_sha256=tree_hash(task))
    manifest['hashes']['scripts/build_workflow_grading_contract_revision.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest['content_hash'] = content_hash(manifest)
    manifest['manifest_id'] = DATASET + '-canonical-' + manifest['content_hash'][:12]
    write_json(destination / 'manifest.json', manifest)
    return manifest


def build(check):
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp)
        manifest = construct(stage)
        expected = {p.relative_to(stage) for p in stage.rglob('*') if p.is_file()}
        output = ROOT / 'datasets' / DATASET
        existing = {p.relative_to(output) for p in output.rglob('*') if p.is_file()}
        if existing - expected:
            raise ValueError('grading_contract_catalog_unexpected_files')
        for relative in sorted(expected):
            path, target = stage / relative, output / relative
            if check:
                if not target.is_file() or target.read_bytes() != path.read_bytes():
                    raise ValueError('grading_contract_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('grading_contract_catalog_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'construction cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
