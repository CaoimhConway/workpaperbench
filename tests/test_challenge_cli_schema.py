"""The local structure checker follows the packaged challenge contract version."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_local_cli_accepts_five_claim_evaluation_reference():
    result = subprocess.run(
        [sys.executable, '-m', 'workpaperbench.cli', 'validate',
         str(ROOT / 'datasets/challenge-v1/tasks/c02/tests/reference.json')],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert 'Output structure valid' in result.stdout
