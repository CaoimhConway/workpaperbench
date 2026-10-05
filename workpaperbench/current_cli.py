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
    manifest, _, task = load(ROOT, task='c03')
    workpaper = json.loads((task / 'tests/reference.json').read_text())
    print('Current authored reference: Block FY2024 revenue and gross-profit reconciliation')
    print('Catalog:', manifest['manifest_id'], 'Scorer:', manifest['scorer_version'])
    for claim in workpaper['answers']:
        print(f"{claim['id']}: {claim['value']:.6f} {claim['unit']}")
    prior = ROOT / 'reports/runs/challenge-v1-evaluation-d9a2fe13f6f2'
    for name in ('final-c03-inexpensive-1','final-c03-reference-1','final-c03-reference-2'):
        saved = json.loads((prior / name / 'answer.json').read_text())
        values = {claim['id']:claim['value'] for claim in saved['answers']}
        print('Historical model submission', name, 'Bitcoin contribution:',
              values['bitcoin_share_of_total_net_revenue_increase_pct'], 'percent')
    print('Contribution to total growth differs from a change in annual revenue share.')
    print('A decimal ratio labeled percent is 100 times too small.')
    print('Source: https://www.sec.gov/Archives/edgar/data/1512673/000162828025007376/sq-20241231.htm')
    print('References and recorded submissions are separate. This display executes no submitted SQL.')


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
