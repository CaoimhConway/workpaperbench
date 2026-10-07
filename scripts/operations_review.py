"""Allow reviewed operational fixes for key-free inspection of the published suite."""
import hashlib
import json
from pathlib import Path
import re

OPERATIONS = {f'scripts/{name}.py' for name in (
    'attempts', 'audit', 'build_real_tasks', 'collect_results', 'fresh_replay',
    'native_run', 'operations_review', 'select_slots',
)}

CORE_PUBLICATION_PATHS = OPERATIONS | {
    '.github/workflows/ci.yml', '.github/workflows/benchmark.yml',
    'workpaperbench/cli.py', 'pyproject.toml', 'DATA_SOURCES.md',
    'scripts/native_trial.py', 'scripts/check_install.py', 'scripts/fix_native_version.py',
}

CHALLENGE_OPERATIONS = {
    'scripts/native_run.py', 'scripts/native_trial.py', 'scripts/check_install.py',
    'scripts/fix_native_version.py', 'scripts/fresh_replay.py', 'scripts/build_challenge_tasks.py',
    'scripts/select_slots.py',
}


def challenge_reviewed_hashes(manifest, root):
    """Permit key-free replay after a versioned operational correction."""
    from select_slots import _repo_file, challenge_dataset_context
    root = Path(root)
    hashes = dict(manifest['hashes'])
    path = root / 'datasets/challenge-v1/operations-review.json'
    if not path.exists():
        return hashes
    review = json.loads(_repo_file(root, 'datasets/challenge-v1/operations-review.json').read_text())
    if review.get('original_manifest_id') != manifest.get('manifest_id'):
        return hashes
    context = challenge_dataset_context(manifest['manifest_id'], root)
    corrections = review.get('correction_hashes')
    if (review.get('original_manifest_sha256') != hashlib.sha256(context['manifest_path'].read_bytes()).hexdigest()
            or not isinstance(corrections, dict) or not corrections
            or not corrections.keys() <= CHALLENGE_OPERATIONS
            or any(name not in hashes or not isinstance(value, str)
                   or not re.fullmatch(r'[0-9a-f]{64}', value)
                   for name, value in corrections.items())):
        raise ValueError('challenge_operations_review_invalid')
    hashes.update(corrections)
    return hashes


def publication_hashes(manifest, root, hashes):
    """Bind shared operational additions while preserving published task/scorer bytes."""
    path = root / 'datasets/challenge-v1/core-review.json'
    if not path.exists():
        return hashes
    from select_slots import _repo_file
    path = _repo_file(root, 'datasets/challenge-v1/core-review.json')
    review = json.loads(path.read_text())
    original = _repo_file(root, 'datasets/real-v1/manifest.json')
    corrections = review.get('correction_hashes', {})
    if (review.get('original_manifest_id') != manifest.get('manifest_id')
            or review.get('original_manifest_sha256') != hashlib.sha256(original.read_bytes()).hexdigest()
            or not isinstance(corrections, dict) or not corrections.keys() <= CORE_PUBLICATION_PATHS
            or any(not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value) for value in corrections.values())):
        raise ValueError('challenge_core_review_invalid')
    hashes.update(corrections)
    return hashes


def reviewed_hashes(manifest, root):
    root = Path(root)
    hashes = dict(manifest['hashes'])
    review_path = root / 'datasets/real-v1/operations-review.json'
    if not review_path.exists():
        return publication_hashes(manifest, root, hashes)
    from select_slots import _repo_file
    review_path = _repo_file(root, 'datasets/real-v1/operations-review.json')
    review = json.loads(review_path.read_text())
    freeze_path = _repo_file(root, 'datasets/real-v1/manifest.json')
    if (review.get('original_manifest_id') != manifest.get('manifest_id')
            or review.get('original_manifest_sha256') != hashlib.sha256(freeze_path.read_bytes()).hexdigest()):
        raise ValueError('operations_review_manifest_mismatch')
    corrections = review.get('correction_hashes')
    if not isinstance(corrections, dict) or not corrections or not corrections.keys() <= OPERATIONS:
        raise ValueError('unauthorized_operations_correction')
    for name, digest in corrections.items():
        if (name != 'scripts/operations_review.py' and name not in hashes
                or not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest)):
            raise ValueError('invalid_operations_correction')
    hashes.update(corrections)
    return publication_hashes(manifest, root, hashes)
