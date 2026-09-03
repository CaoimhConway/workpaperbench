"""Freeze the one real-v1 snapshot after source and engineering review."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from select_slots import manifest_content_hash

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / 'datasets/real-v1'


def freeze():
    destination = DATASET / 'manifest.json'
    if destination.exists():
        raise ValueError('The real-v1 manifest is already frozen. Do not replace a published identity.')
    tasks = {}
    for path in sorted((DATASET / 'sources').glob('wp*.json')):
        definition = json.loads(path.read_text())
        tasks[path.stem] = {key: definition[key] for key in ('task_id', 'split', 'origin', 'source_group', 'previously_exposed')}
        tasks[path.stem]['path'] = 'datasets/real-v1/tasks/' + path.stem
        tasks[path.stem]['reference'] = tasks[path.stem]['path'] + '/tests/reference.json'
        tasks[path.stem]['control_origin'] = definition['control_origin']
    if set(tasks) != {f'wp0{i}' for i in range(1, 9)} or sum(t['origin'] == 'deterministic_source_derived' for t in tasks.values()) != 6:
        raise ValueError('The freeze requires exactly eight tasks and six genuine source-derived base tasks')
    paths = [p for p in DATASET.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [ROOT / name for name in (
        'config/runtime.json', 'config/skills/contract-check/SKILL.md', 'pyproject.toml',
        'workpaperbench/grading.py', 'workpaperbench/sql_worker.py', 'workpaperbench/cli.py',
        'workpaperbench/real_report.py', '.github/workflows/ci.yml', '.github/workflows/benchmark.yml',
        'scripts/build_real_tasks.py', 'scripts/real_definitions.py', 'scripts/freeze_real.py',
        'scripts/capture_real.py', 'scripts/real_controls.py', 'scripts/fresh_replay.py',
        'scripts/native_run.py', 'scripts/native_trial.py', 'scripts/select_slots.py',
        'scripts/attempts.py', 'scripts/collect_results.py', 'scripts/fix_native_version.py',
        'scripts/audit.py', 'DATA_SOURCES.md',
    )]
    # Reused source definitions are themselves frozen dependencies of reconstruction.
    paths += [ROOT / 'sources' / (identifier + '.json') for identifier in ('wp01', 'wp02', 'wp05', 'wp07')]
    hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
    runtime = json.loads((ROOT / 'config/runtime.json').read_text())
    manifest = {
        'dataset_id': 'real-v1', 'frozen_at': datetime.now(timezone.utc).isoformat(),
        'schedule': 'datasets/real-v1/schedule.json', 'pilot': 'datasets/real-v1/pilot.json',
        'schema': 'datasets/real-v1/schema.json', 'tasks': tasks,
        'source_groups': {key: task['source_group'] for key, task in tasks.items()},
        'model': runtime['model']['id'], 'model_route': runtime['model']['route_policy'],
        'runtime': 'config/runtime.json', 'scorer_version': '1.2.0',
        'scorer_sha256': hashlib.sha256((ROOT / 'workpaperbench/grading.py').read_bytes() + (ROOT / 'workpaperbench/sql_worker.py').read_bytes()).hexdigest(),
        'treatment': {'path': 'config/skills/contract-check/SKILL.md', 'sha256': hashes['config/skills/contract-check/SKILL.md'], 'A': 'Full common instructions', 'B': 'Identical common inputs plus the preserved contract-check skill'},
        'evidence_contract': 'Per claim, declared before freeze, with reviewed equivalent context paths',
        'budget': {'final_slots': 48, 'pilot_slots': 2, 'maximum_pilot_slots': 6,
                   'cumulative_inference_authorization_usd': 50, 'existing_dedicated_lifetime_cap_usd': 20,
                   'historical_provider_lifetime_usd': 0.769789131, 'incremental_actions_ceiling_usd': 10},
        'hashes': hashes,
    }
    manifest['content_hash'] = manifest_content_hash(manifest)
    manifest['manifest_id'] = 'real-v1-' + manifest['content_hash'][:12]
    destination.write_text(json.dumps(manifest, indent=2) + '\n')
    print(manifest['manifest_id'])


if __name__ == '__main__':
    freeze()
