"""Review publication contexts and verify frozen files without secret output."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
patterns = [rb'sk-or-v1-[a-zA-Z0-9]{20,}', rb'gh[pousr]_[a-zA-Z0-9]{20,}', rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).split(b'\0')
failures = []
for raw in tracked:
    if not raw:
        continue
    path = ROOT / raw.decode()
    data = path.read_bytes()
    if any(re.search(pattern, data) for pattern in patterns):
        failures.append(str(path.relative_to(ROOT)) + ':credential_pattern')
for dockerfile in (ROOT / 'tasks').glob('*/environment/Dockerfile'):
    text = dockerfile.read_text()
    if 'COPY . ' in text or 'gold' in text or '.git' in text or 'OPENROUTER_API_KEY' in text:
        failures.append(str(dockerfile.relative_to(ROOT)) + ':candidate_context')
for obj in subprocess.check_output(['git','rev-list','--objects','--all'],cwd=ROOT).splitlines():
    sha = obj.split(b' ')[0]
    kind = subprocess.check_output(['git','cat-file','-t',sha],cwd=ROOT).strip()
    if kind != b'blob':
        continue
    content = subprocess.check_output(['git','cat-file','blob',sha],cwd=ROOT)
    if any(re.search(pattern,content) for pattern in patterns):
        failures.append('history:credential_pattern')
freeze = ROOT / 'config/freeze.json'
if freeze.exists():
    manifest = json.loads(freeze.read_text())
    expected_hashes = dict(manifest['hashes'])
    review_path = ROOT / 'config/review.json'
    if review_path.exists():
        review = json.loads(review_path.read_text())
        if review['original_manifest_id'] != manifest['manifest_id'] or hashlib.sha256(freeze.read_bytes()).hexdigest() != review['original_freeze_sha256']:
            failures.append('original_freeze_changed')
        # Candidate-facing evidence, task requests, reference answers and treatment
        # stay fixed. Only reviewed implementation hashes can supersede code hashes.
        for name, expected in manifest['hashes'].items():
            immutable = name.startswith('sources/') or name.startswith('config/') or (
                name.startswith('tasks/') and '/workpaperbench/' not in name)
            if immutable and hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
                failures.append(name + ':candidate_or_reference_changed')
        expected_hashes.update(review['correction_hashes'])
    for name, expected in expected_hashes.items():
        path = ROOT / name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(name + ':versioned_hash_mismatch')
if failures:
    print('\n'.join(failures))
    raise SystemExit(1)
print('Publication checks passed. Original candidate inputs and versioned implementation hashes verified.')
