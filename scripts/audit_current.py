"""Audit publication contexts and current benchmark catalogs."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workpaperbench.catalog import load


def main():
    subprocess.run([sys.executable, str(ROOT / 'scripts/audit.py')],
                   cwd=ROOT, check=True)
    for dataset in ('challenge-v2', 'workflow-v1', 'workflow-v2', 'workflow-v3',
                    'workflow-v4', 'workflow-v5', 'workflow-v6', 'workflow-v7',
                    'workflow-v8'):
        manifest = load(ROOT, dataset)
        for key in manifest['tasks']:
            load(ROOT, dataset, key)
    print('Publication checks passed for current catalogs and retained historical benchmark inputs.')


if __name__ == '__main__':
    main()
