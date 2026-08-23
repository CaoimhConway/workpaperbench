"""Allow reviewed operational fixes for key-free inspection of the published suite."""
import hashlib
import json
from pathlib import Path
import re
import copy

OPERATIONS = {f'scripts/{name}.py' for name in (
    'attempts', 'audit', 'build_real_tasks', 'collect_results', 'fresh_replay',
    'native_run', 'operations_review', 'select_slots',
)}

CORE_PUBLICATION_PATHS = OPERATIONS | {
    '.github/workflows/ci.yml', '.github/workflows/benchmark.yml',
    'workpaperbench/cli.py', 'pyproject.toml', 'DATA_SOURCES.md',
    'scripts/native_trial.py', 'scripts/check_install.py', 'scripts/fix_native_version.py',
    'scripts/real_controls.py',
}

CHALLENGE_OPERATIONS = {
    'scripts/native_run.py', 'scripts/native_trial.py', 'scripts/check_install.py',
    'scripts/fix_native_version.py', 'scripts/fresh_replay.py', 'scripts/build_challenge_tasks.py',
    'scripts/select_slots.py',
}


PUBLICATION_INPUTS = {
    f'{prefix}{section}/{task}{suffix}'
    for prefix, tasks in (('', ('wp04', 'wp05', 'wp08')),
                          ('datasets/real-v1/', ('wp05',)))
    for task in tasks
    for section, suffix in (
        ('sources', '.json'), ('tasks', '/environment/evidence.json'),
        ('tasks', '/environment/sources.md'), ('tasks', '/tests/evidence.json'),
        ('tasks', '/tests/sources.md'), ('tasks', '/tests/gold.json'))
}


def context_contract(text):
    """Exclude only historical motivation prose from the financial definitions."""
    text = text.rstrip()
    if text.startswith('# Export delivery note'):
        return '\n\n'.join(text.split('\n\n')[:2])
    if text.startswith('# Shared USDC window fixture'):
        text = re.sub(r'This is an explicitly synthetic [^.]+\. It contains', 'It contains', text, count=1)
        text = re.sub(r' max_per_tx does not reproduce [^.]+\.', '', text, count=1)
        text = re.sub(r' Public methodology motivation only: https?://\S+ \.', '', text, count=1)
        return text
    raise ValueError('publication_context_not_supported')


def publication_contract(name, data):
    """Hash all substantive fields, excluding the approved presentation fields."""
    if name.endswith('/sources.md'):
        content = context_contract(data.decode())
    else:
        content = copy.deepcopy(json.loads(data))
        if '/sources/' in '/' + name:
            content['context'] = context_contract(content['context'])
            evidence = content['evidence']
        elif name.endswith('/evidence.json'):
            evidence = content
        else:
            evidence = []
            for field in ('evidence.json', 'sources.md'):
                content['hashes'].pop(field)
        for entry in evidence:
            if entry['id'] == 'methodology:context':
                entry.pop('origin')
    return hashlib.sha256(json.dumps(content, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def publication_input_hashes(manifest, root, hashes=None):
    """Validate explicitly bound publication copies for key-free inspection only."""
    root = Path(root)
    hashes = dict(manifest['hashes'] if hashes is None else hashes)
    registry_path = root / 'config/publication-inputs.json'
    if not registry_path.exists():
        return hashes
    def publication_file(name):
        path = root / name
        if (not path.is_file() or path.is_symlink()
                or any(parent.is_symlink() for parent in path.parents if parent != root.parent)):
            raise ValueError('publication_file_invalid:' + name)
        return path

    registry = json.loads(publication_file('config/publication-inputs.json').read_text())
    identity = manifest.get('manifest_id')
    if identity not in registry['manifests']:
        return hashes
    entry = registry['manifests'][identity]
    manifest_path = {
        'wpb-v1-92baa4a72f0e': 'config/freeze.json',
        'real-v1-76d0ba6152ff': 'datasets/real-v1/manifest.json',
        'challenge-v1-development-7e8903385beb': 'datasets/challenge-v1/manifests/development.json',
        'challenge-v1-evaluation-d9a2fe13f6f2': 'datasets/challenge-v1/manifests/evaluation.json',
    }[identity]
    if entry['original_manifest_sha256'] != hashlib.sha256(publication_file(manifest_path).read_bytes()).hexdigest():
        raise ValueError('publication_manifest_mismatch')
    expected_paths = PUBLICATION_INPUTS & manifest['hashes'].keys()
    if set(entry['inputs']) != expected_paths:
        raise ValueError('publication_input_allowlist')
    for name, binding in entry['inputs'].items():
        data = publication_file(name).read_bytes()
        if (binding['original_sha256'] != manifest['hashes'][name]
                or binding['publication_sha256'] != hashlib.sha256(data).hexdigest()
                or binding['contract_sha256'] != publication_contract(name, data)):
            raise ValueError('publication_input_mismatch:' + name)
        hashes[name] = binding['publication_sha256']
    documents = entry.get('documents', {})
    allowed_docs = {'build-notes/NATIVE_COMPATIBILITY.md', 'third-party/NOTICE.md'} & manifest['hashes'].keys()
    if set(documents) != allowed_docs:
        raise ValueError('publication_document_allowlist')
    for name, binding in documents.items():
        if (binding['original_sha256'] != manifest['hashes'][name]
                or binding['publication_sha256'] != hashlib.sha256(publication_file(name).read_bytes()).hexdigest()):
            raise ValueError('publication_document_mismatch')
        hashes[name] = binding['publication_sha256']
    implementations = entry.get('implementations', {})
    if not implementations.keys() <= {'scripts/audit.py', 'scripts/operations_review.py',
                                      'scripts/real_controls.py', 'DATA_SOURCES.md'}:
        raise ValueError('publication_implementation_allowlist')
    for name, binding in implementations.items():
        if (binding['original_sha256'] != manifest['hashes'].get(name)
                or binding['publication_sha256'] != hashlib.sha256(publication_file(name).read_bytes()).hexdigest()):
            raise ValueError('publication_implementation_mismatch')
        hashes[name] = binding['publication_sha256']
    return hashes


def challenge_reviewed_hashes(manifest, root):
    """Permit key-free replay after a versioned operational correction."""
    from select_slots import _repo_file, challenge_dataset_context
    root = Path(root)
    hashes = dict(manifest['hashes'])
    path = root / 'datasets/challenge-v1/operations-review.json'
    if not path.exists():
        return publication_input_hashes(manifest, root, hashes)
    review = json.loads(_repo_file(root, 'datasets/challenge-v1/operations-review.json').read_text())
    if review.get('original_manifest_id') != manifest.get('manifest_id'):
        return publication_input_hashes(manifest, root, hashes)
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
    return publication_input_hashes(manifest, root, hashes)


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
        return publication_input_hashes(manifest, root, publication_hashes(manifest, root, hashes))
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
    return publication_input_hashes(manifest, root, publication_hashes(manifest, root, hashes))
