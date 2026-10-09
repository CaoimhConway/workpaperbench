"""Freeze unambiguous claims and declared output labels without changing financial inputs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workpaperbench.catalog import content_hash, load, tree_hash
from review_workflow import SCORER, reviewed_task, seal, write_json

DATASET = 'workflow-v6'
REVIEW = 'config/workflow-claim-review.json'
CLAIM_POLICY = ('Supported means the supplied evidence entails the assertion. Contradicted means it entails the negation. '
    'Unresolved means neither follows. A claim that the supplied dossier explicitly reports a quantity is contradicted '
    'when the supplied scope explicitly omits it. A claim about the unknown economic quantity itself remains unresolved. '
    'Do not infer zero from missing information. No label count or order is promised.')
TEXT_POLICY = ('Text columns declare canonical values and accepted source-label aliases. Aliases refer to the same '
    'economic category, never a different period, unit or measure. Duplicate keys after normalization fail. '
    'Different SQL, row order and column order are accepted. Numeric tolerances are unchanged.')
EVIDENCE_POLICY = ('Cite sufficient supporting source IDs for each output. IDs may appear alone or inside explanations, '
    'with multiple IDs in one entry. Explanation-only entries do not supply evidence. Every cited ID must be relevant '
    'and known. Additional unrelated sections fail. Prose is not an entailment check and cannot repair incorrect numbers.')


def construct(destination):
    prior = load(ROOT, 'workflow-v5')
    review = json.loads((ROOT / REVIEW).read_text())
    if review['base_catalog'] != prior['manifest_id']:
        raise ValueError('claim_review_base_changed')
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
        scorer_version='workflow-1.2.0', scorer_path=SCORER,
        scorer_sha256=hashlib.sha256((ROOT / SCORER).read_bytes()).hexdigest(),
        status='Software and authored controls only, no candidate runs on revised tasks',
        validity_revision={'review': REVIEW, 'new_inference': False,
                           'financial_inputs_changed': False, 'claim_contract_changed': True})
    for key, old in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v5', key)
        task = destination / 'tasks' / key
        gold = reviewed_task(source, task, key, historical=False)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(old['task_id'], identifier))
        gold['task_id'] = identifier
        contract = json.loads((task / 'environment/output_contract.json').read_text())
        replacement = review['claims'][key]
        removed = [name for name, spec in gold['claims'].items() if spec['verdict'] == 'unresolved']
        if len(removed) != 1 or replacement['replaces'] != removed[0]:
            raise ValueError('claim_review_target_changed:' + key)
        contract['claim_assertions'][removed[0]] = replacement['assertion']
        gold['claims'][removed[0]] = {field: replacement[field]
            for field in ('verdict', 'evidence', 'context_evidence_allowed')}
        # Opaque, deterministically permuted IDs remove the fixed uncertainty slot.
        order = sorted(gold['claims'], key=lambda name: hashlib.sha256((key + ':' + name).encode()).digest())
        mapping = {old_name: 'claim_' + str(i + 1) for i, old_name in enumerate(order)}
        gold['claims'] = {mapping[name]: gold['claims'][name] for name in order}
        contract['claim_assertions'] = {mapping[name]: contract['claim_assertions'][name] for name in order}
        contract['claim_policy'], contract['text_policy'], contract['evidence_policy'] = CLAIM_POLICY, TEXT_POLICY, EVIDENCE_POLICY
        for name, spec in gold['tables'].items():
            contract['tables'][name]['columns'] = spec['columns']
        if key == 'a01':
            contract['definitions']['quarter_reconciliation'] = 'margin_qoq_bps = 10000 * (Q2 operating income / Q2 revenue - Q1 operating income / Q1 revenue). Both ratios use matching consolidated quarters and units.'
        write_json(task / 'environment/output_contract.json', contract)
        reference = json.loads((task / 'tests/reference.json').read_text())
        reference['claims'] = [{'id': name, 'verdict': spec['verdict'], 'evidence': spec['evidence'][0]}
                               for name, spec in gold['claims'].items()]
        write_json(task / 'tests/reference.json', reference)
        instruction = (task / 'instruction.md').read_text()
        old_contract = json.loads((source / 'environment/output_contract.json').read_text())
        instruction = instruction.replace(old_contract['evidence_policy'], EVIDENCE_POLICY)
        instruction = instruction.replace('and whether a separate price effect is identifiable.', 'and assess the stated claim about the contribution of higher Bitcoin prices.')
        instruction = instruction.replace('Table column names are required,', CLAIM_POLICY + '\n\n' + TEXT_POLICY + '\n\nTable column names are required,')
        (task / 'instruction.md').write_text(instruction)
        solve = '#!/bin/bash\nset -euo pipefail\n'
        for table in reference['tables']:
            solve += "cat > /logs/artifacts/" + table['file'] + " <<'SQL'\n" + (task / 'solution' / table['file']).read_text() + 'SQL\n'
        solve += "cat > /logs/artifacts/answer.json <<'ANSWER'\n" + json.dumps(reference, indent=2) + '\nANSWER\n'
        (task / 'solution/solve.sh').write_text(solve)
        seal(task, gold)
        authoring = json.loads((task / 'authoring.json').read_text())
        authoring['validity_revision'] = {'prior_task_sha256': old['task_sha256'], 'claim_mapping': mapping,
                                         'replacement_review': replacement, 'human_review': 'pending'}
        write_json(task / 'authoring.json', authoring)
        manifest['tasks'][key].update(task_id=identifier, path='datasets/' + DATASET + '/tasks/' + key,
                                     task_sha256=tree_hash(task))
    for name in (SCORER, REVIEW, 'scripts/build_workflow_validity.py', 'scripts/review_workflow.py'):
        manifest['hashes'][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    manifest['content_hash'] = content_hash(manifest)
    manifest['manifest_id'] = DATASET + '-canonical-' + manifest['content_hash'][:12]
    write_json(destination / 'manifest.json', manifest)
    return manifest


def build(check):
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp)
        manifest = construct(stage)
        for path in stage.rglob('*'):
            if not path.is_file():
                continue
            target = ROOT / 'datasets' / DATASET / path.relative_to(stage)
            if check:
                if not target.is_file() or target.read_bytes() != path.read_bytes():
                    raise ValueError('validity_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('validity_catalog_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
