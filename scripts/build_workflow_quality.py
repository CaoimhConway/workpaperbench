"""Freeze reviewed evidence scopes and informative financial reconciliation controls."""
import argparse
import copy
from decimal import Decimal
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
from build_workflow_tasks import observations, specifications as prototypes, write_json
from build_workflow_suite import specifications, evaluation_specifications

DATASET = 'workflow-v5'
SCORER = 'config/scorers/workflow-1.1.0.py'
REVIEW = 'config/workflow-quality-review.json'


def project_rows(tables, keep):
    return {name: [[row[index] for index in keep[name]] for row in rows]
            for name, rows in tables.items()}


def calculate_control(key, calculator, data):
    expected = calculator(data)
    if key == 'a05':
        facts = {(row['fiscal_year'], row['weeks']): row for row in data['income']}
        def reported(year, weeks):
            def amount(duration):
                return Decimal(str(facts[year, duration]['operating_income_usd_million']))
            return amount(52) - amount(16) if weeks == 36 else amount(weeks)
        for row in expected['operating_growth_bridge']:
            delta = reported(2025, row[0]) - reported(2024, row[0])
            row[-1] = float(Decimal(100) * Decimal(str(row[-2])) / delta)
    return expected


def construct(destination):
    prior = load(ROOT, 'workflow-v4')
    review = json.loads((ROOT / REVIEW).read_text())
    if review['base_catalog'] != prior['manifest_id']:
        raise ValueError('quality_review_base_changed')
    calculators = {**prototypes(), **specifications(), **evaluation_specifications()}
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
        scorer_version='workflow-1.1.0', scorer_path=SCORER,
        scorer_sha256=hashlib.sha256((ROOT / SCORER).read_bytes()).hexdigest(),
        status='Reviewed source selection and discrepancy controls, candidate-model evaluation pending',
        quality_revision={'review': REVIEW, 'removed_identity_columns': 3,
                          'discrepancy_columns': 51, 'new_inference': False})
    for key, original in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v4', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(original['task_id'], identifier))
        gold = json.loads((task / 'tests/gold.json').read_text())
        gold['scorer_version'] = 'workflow-1.1.0'
        gold.pop('context_evidence_allowed', None)
        available = {entry['id'] for entry in json.loads((task / 'environment/evidence.json').read_text())}
        unused = set(review['additional_context'][key]) - set(gold['tables']) - set(gold['claims'])
        if unused:
            raise ValueError('unknown_context_output:' + key)
        for role in ('tables', 'claims'):
            for name, spec in gold[role].items():
                extra = review['additional_context'][key].get(name, [])
                if not set(extra) <= available:
                    raise ValueError('unknown_context_source:' + key)
                spec['context_evidence_allowed'] = extra
        keep = {}
        removed = review['removed_identity_columns'].get(key, {})
        for name, spec in gold['tables'].items():
            columns = list(spec['columns'])
            drop = set(removed.get(name, []))
            keep[name] = [i for i, column in enumerate(columns) if column not in drop]
            if not drop:
                continue
            spec['columns'] = {column: value for column, value in spec['columns'].items() if column not in drop}
            spec['rows'] = [[row[index] for index in keep[name]] for row in spec['rows']]
            selected = ', '.join('"' + column + '"' for column in spec['columns'])
            for path in (task / 'solution' / (name + '.sql'), task / 'environment' / ('starting_' + name + '.sql')):
                original_sql = path.read_text().strip().rstrip(';')
                path.write_text('SELECT ' + selected + ' FROM (\n' + original_sql + '\n) AS workpaper\n')
        for control in gold['controls']:
            control['tables'] = project_rows(control['tables'], keep)
        control_review = review['residual_controls'].get(key, {})
        changes = control_review.get('changes', [])
        if changes:
            calculator = calculators[key]
            facts = ROOT / 'datasets/workflow-v2/observations' / calculator['source'] / 'facts.json'
            original_data = observations(source / 'tests/data.sqlite')
            data = json.loads(facts.read_text()) if facts.is_file() else copy.deepcopy(original_data)
            if data != original_data:
                raise ValueError('source_fact_rows_differ:' + key)
            filename = 'control-discrepancy.sqlite'
            shutil.copyfile(task / 'tests/data.sqlite', task / 'tests' / filename)
            with sqlite3.connect(task / 'tests' / filename) as connection:
                for table, index, column, delta in changes:
                    row = data[table][index]
                    before = row[column]
                    row[column] += delta
                    actual = connection.execute('SELECT "' + column + '" FROM "' + table + '" WHERE rowid=?', (index + 1,)).fetchone()
                    if actual != (before,):
                        raise ValueError('counterfactual_row_identity_changed:' + key)
                    connection.execute('UPDATE "' + table + '" SET "' + column + '"=? WHERE rowid=?', (row[column], index + 1))
            expected = project_rows(calculate_control(key, calculator['calculate'], data), keep)
            gold['controls'].append({'name': 'independent_disclosure_discrepancy', 'database': filename,
                'origin': 'authored_synthetic_counterfactual', 'changes': changes, 'tables': expected})
        shutil.copyfile(ROOT / SCORER, task / 'tests/workpaperbench/workflow_grading.py')
        contract_path = task / 'environment/output_contract.json'
        contract = json.loads(contract_path.read_text())
        for name, spec in gold['tables'].items():
            contract['tables'][name]['columns'] = spec['columns']
        if key == 'a05':
            contract['definitions']['operating_growth_bridge'] = 'Changes are FY2025 less FY2024 for each matched duration. SG&A is a signed negative contribution. The denominator is the change in independently reported operating income for that duration, even when reconstructed component totals disagree.'
        contract['evidence_policy'] = 'Cite sufficient facts and relevant period, unit, definition or scope context for each output. Additional unrelated sections fail evidence. Equivalent reviewed source paths are accepted, without a shortest-citation requirement.'
        contract['reconciliation_policy'] = 'Residuals compare independently supplied observations. Synthetic controls may make reported totals and components disagree. Preserve the discrepancy instead of forcing zero or changing a source observation. Algebraic identity residuals are not requested.'
        write_json(contract_path, contract)
        instruction = (task / 'instruction.md').read_text()
        instruction = instruction.replace('Cite each output\'s supporting evidence IDs.', contract['evidence_policy'])
        instruction = instruction.replace('Reconcile quarter totals to six-month statements, calculate', 'Derive the first quarter from six-month statements, calculate')
        prefix = instruction.split('Recompute from pristine inputs.', 1)[0]
        control_text = 'Recompute from pristine inputs. Hidden synthetic controls exercise period filters, equivalent monetary scaling, component changes and unaffected outputs. Reported totals and components may disagree, and independently observed residuals must retain the discrepancy. Do not silently repair source observations. Conclusions refer to the original dossier only.'
        if key == 'b01':
            control_text += ' Duplicate exports count once, while different economic dates remain distinct even when their amounts are equal.'
        (task / 'instruction.md').write_text(prefix + control_text + '\n\nTask ID: ' + identifier + '\n')
        reference = json.loads((task / 'tests/reference.json').read_text())
        solve = '#!/bin/bash\nset -euo pipefail\n'
        for table in reference['tables']:
            sql = (task / 'solution' / table['file']).read_text()
            solve += "cat > /logs/artifacts/" + table['file'] + " <<'SQL'\n" + sql + 'SQL\n'
        solve += "cat > /logs/artifacts/answer.json <<'ANSWER'\n" + json.dumps(reference, indent=2) + '\nANSWER\n'
        (task / 'solution/solve.sh').write_text(solve)
        gold['hashes'] = {path.relative_to(task / 'tests').as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in sorted((task / 'tests').rglob('*')) if path.is_file() and path.name not in ('gold.json', 'reference.json')}
        write_json(task / 'tests/gold.json', gold)
        authoring = json.loads((task / 'authoring.json').read_text())
        authoring['quality_revision'] = {'prior_task_sha256': original['task_sha256'],
            'evidence': 'Reviewed per-output support and additional context, unrelated sections rejected',
            'removed_identity_columns': removed, 'new_synthetic_control': bool(changes), 'reference_correction': review.get('reference_corrections', {}).get(key), 'human_review': 'pending'}
        write_json(task / 'authoring.json', authoring)
        manifest['tasks'][key].update(task_id=identifier, path='datasets/' + DATASET + '/tasks/' + key,
                                     task_sha256=tree_hash(task))
    for name in (SCORER, REVIEW, 'scripts/build_workflow_quality.py'):
        manifest['hashes'][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
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
                    raise ValueError('workflow_quality_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('workflow_quality_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
