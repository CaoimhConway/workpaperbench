"""Allow reviewed operational fixes for key-free inspection of the published suite."""
import hashlib
import json
from pathlib import Path
import re

OPERATIONS = {f'scripts/{name}.py' for name in (
    'attempts', 'audit', 'build_real_tasks', 'collect_results', 'fresh_replay',
    'native_run', 'operations_review', 'select_slots',
)}


def reviewed_hashes(manifest, root):
    root = Path(root)
    hashes = dict(manifest['hashes'])
    review_path = root / 'datasets/real-v1/operations-review.json'
    if not review_path.exists():
        return hashes
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
    return hashes
