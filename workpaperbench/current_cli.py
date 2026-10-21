"""Construct and verify financial workpapers with the native evaluation harness."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator
from .catalog import load
from .grading import parse, validate
from .workflow_report import summarize

ROOT = Path(__file__).resolve().parents[1]


def demo():
    manifest, _, task = load(ROOT, 'workflow-v11', 'c01')
    gold = json.loads((task / 'tests/gold.json').read_text())
    bridge = gold['tables']['revenue_bridge']
    row = next(row for row in bridge['rows'] if row[0] == 'bitcoin')
    contribution = row[list(bridge['columns']).index('contribution_pct')]
    print('Authored reference: Block FY2024 revenue and gross-profit reconciliation')
    print('Catalog:', manifest['manifest_id'], 'Scorer:', manifest['scorer_version'])
    print('Construction track: write all three queries from supplied evidence. No starting SQL.')
    print(f'Bitcoin contribution to consolidated revenue growth: {contribution:.6f} percent')
    print('100 * (10,199,205 - 9,498,302) / (24,121,053 - 21,915,623)')
    print('A change in annual revenue share measures a different quantity.')
    print('A decimal ratio labeled percent is 100 times too small.')
    report = json.loads((ROOT / 'reports/workflow-v5/corrected-replay.json').read_text())
    baselines = json.loads((ROOT / 'reports/workflow-v7/starting-sql.json').read_text())['baselines']
    maintenance = load(ROOT, 'workflow-v7')
    current = [row for row in baselines if row['manifest_id'] == maintenance['manifest_id']]
    passed = sum(table['original'] and all(table['controls'].values())
                 for row in current for table in row['tables'].values())
    print(f'Separate maintenance track (v7): {passed}/90 supplied queries already pass original inputs and controls.')
    print('Historical maintenance evidence: corrected workflow-v5 replays of unchanged submissions:')
    for row in report['attempts']:
        checks = row['verdict']['checks']
        print(row['attempt_id'], 'numbers:', checks['numerical_tables'],
              'claims:', checks['claim_verdicts'], 'evidence:', checks['evidence'],
              'robustness:', checks['robustness'], 'delivery:', checks['delivery'])
        comparison = summarize({**row, 'manifest_id': report['base_manifest_id'],
            'scorer_sha256': report['scorer_sha256'], 'task_id': 'workflow-v5-' + row['task'],
            'task_sha256': row['reviewed_task_sha256'], 'status': 'verified'}, baselines)
        print('  Original inputs plus controls:', comparison['transition_counts']['original_and_controls'])
    print('No new inference. Unequal historical budgets. These are not construction-track model results.')
    print('This display reads authored targets and recorded receipts. It executes no submitted SQL.')


def main():
    arguments = sys.argv[1:] or ['demo']
    if arguments[0] == 'guest':
        raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts/guest_bench.py'), *arguments[1:]]))
    if arguments[0] in ('preflight', 'run', 'grade', 'report', 'smoke', 'list', 'batch'):
        raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts/guest_bench.py'), *arguments]))
    if arguments[0] in ('local','serve','replay','controls','queue'):
        arguments = arguments[1:] if arguments[0] == 'local' else arguments
        raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts/local_bench.py'), *arguments]))
    if arguments[0] == 'legacy':
        from .cli import main as historical_main
        sys.argv = [sys.argv[0], *arguments[1:]]
        historical_main()
        return
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    sub.add_parser('demo',help='Show a reference and preserved historical submissions')
    for name,description in (
        ('guest','Alias for the portable native harness'),
        ('local','Use the owner-specific historical Mac/Lima profile'),
        ('preflight','Check Linux, Docker and the pinned native harness'),
        ('serve','Start one pinned local model'),
        ('list','List development or evaluation tasks'),
        ('run','Run your configured model on any task with fresh candidate state'),
        ('batch','Run a selected split or task list with the same configuration'),
        ('smoke','Check native tool delivery using a scripted fixture, without inference'),
        ('grade','Verify a supplied workpaper without inference'),
        ('replay','Freshly verify retained artifacts without inference'),
        ('report','Write an immutable versioned result report'),
        ('queue','Run a declared local development queue with checkpoints'),
        ('controls','Test the actual local isolation and SQL limits'),
        ('legacy','Use the frozen historical interface'),
    ):
        sub.add_parser(name,help=description)
    checking = sub.add_parser('validate',help='Check output structure without executing SQL')
    checking.add_argument('path',type=Path)
    args = parser.parse_args(arguments)
    if args.command == 'demo':
        demo()
        return
    answer = parse(args.path.read_bytes())
    identifier = str(answer.get('task_id',''))
    dataset = identifier.rsplit('-',1)[0] if identifier.startswith('workflow-') else 'challenge-v2'
    _, _, task = load(ROOT, dataset, identifier.removeprefix(dataset+'-'))
    schema = json.loads((task / 'environment/schema.json').read_text())
    if dataset.startswith('workflow-'):
        Draft202012Validator(schema).validate(answer)
    else:
        validate(answer,schema)
    print('Output structure valid. Financial correctness requires fresh separate verification.')


if __name__ == '__main__':
    main()
