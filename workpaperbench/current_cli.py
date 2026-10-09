"""Current local workpapers and explicit historical reproduction."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator
from .catalog import load
from .grading import parse, validate

ROOT = Path(__file__).resolve().parents[1]


def demo():
    manifest, _, task = load(ROOT, 'workflow-v6', 'c01')
    gold = json.loads((task / 'tests/gold.json').read_text())
    bridge = gold['tables']['revenue_bridge']
    row = next(row for row in bridge['rows'] if row[0] == 'bitcoin')
    contribution = row[list(bridge['columns']).index('contribution_pct')]
    print('Authored reference: Block FY2024 revenue and gross-profit reconciliation')
    print('Catalog:', manifest['manifest_id'], 'Scorer:', manifest['scorer_version'])
    print(f'Bitcoin contribution to consolidated revenue growth: {contribution:.6f} percent')
    print('100 * (10,199,205 - 9,498,302) / (24,121,053 - 21,915,623)')
    print('A change in annual revenue share measures a different quantity.')
    print('A decimal ratio labeled percent is 100 times too small.')
    report = json.loads((ROOT / 'reports/workflow-v5/corrected-replay.json').read_text())
    print('Corrected workflow-v5 replays of unchanged retained development submissions:')
    for row in report['attempts']:
        checks = row['verdict']['checks']
        print(row['attempt_id'], 'numbers:', checks['numerical_tables'],
              'claims:', checks['claim_verdicts'], 'evidence:', checks['evidence'],
              'robustness:', checks['robustness'], 'delivery:', checks['delivery'])
    print('No new inference. These are not workflow-v6 model results.')
    print('This display reads authored targets and recorded receipts. It executes no submitted SQL.')


def main():
    arguments = sys.argv[1:] or ['demo']
    if arguments[0] in ('local','preflight','serve','run','grade','replay','report','controls','queue'):
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
        ('preflight','Check the local execution host and guest'),
        ('serve','Start one pinned local model'),
        ('run','Run selected development tasks with fresh candidate state'),
        ('grade','Verify a bounded engineer workpaper without inference'),
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
