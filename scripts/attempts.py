"""Write receipts before setup and preserve incomplete attempts after failures."""
import json
import os
import re
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def record_directory(manifest_id, identifier, root=None):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}', manifest_id):
        raise ValueError('invalid_experiment_identifier')
    from select_slots import SLOT_PATTERN
    if not re.fullmatch(SLOT_PATTERN, identifier):
        raise ValueError('invalid_slot_identifier')
    return (ROOT if root is None else Path(root)) / 'reports/runs' / manifest_id / identifier


def check(mode, manifest_id, identifiers):
    from select_slots import history
    if os.environ.get('GITHUB_RUN_ATTEMPT') != '1':
        raise ValueError('same_run_retry_disabled')
    attempted = history(mode, manifest_id)
    for identifier in identifiers:
        if identifier in attempted:
            raise ValueError('slot_previously_attempted')
        data = json.loads((record_directory(manifest_id, identifier) / 'record.json').read_text())
        if (str(data.get('run_id')) != os.environ.get('GITHUB_RUN_ID')
                or str(data.get('github_run_attempt')) != '1'
                or data.get('experiment_id') != manifest_id
                or data.get('status') != 'setup_started'):
            raise ValueError('attempt_receipt_mismatch')
    return attempted


def receipt(mode, manifest_id, identifiers):
    from select_slots import challenge_dataset_context, real_dataset_context, selection
    if os.environ.get('GITHUB_RUN_ATTEMPT') != '1':
        raise ValueError('same_run_retry_disabled')
    available, _ = selection(mode, manifest_id, 'all')
    context = challenge_dataset_context(manifest_id, ROOT)
    if context is None:
        context = real_dataset_context(manifest_id, ROOT)
    by_id = {s['slot_id']: s for s in available}
    if not identifiers or len(identifiers) > 2 or any(i not in by_id for i in identifiers):
        raise ValueError('slot_previously_attempted_or_invalid')
    for index, identifier in enumerate(identifiers):
        path = record_directory(manifest_id, identifier) / 'record.json'
        if path.exists():
            raise ValueError('existing_attempt_record')
        data = {**by_id[identifier], 'experiment_id': manifest_id,
                'freeze_manifest_id': manifest_id if mode == 'final' else None,
                'status': 'setup_started', 'started_at': now(), 'verdict': None,
                'remaining_planned_slots': len(available) - index,
                'run_id': os.environ['GITHUB_RUN_ID'],
                'github_run_attempt': os.environ['GITHUB_RUN_ATTEMPT'],
                'commit_sha': os.environ['GITHUB_SHA']}
        if context is not None:
            data.update(dataset_id=context['dataset_id'],
                        dataset_manifest_id=context['manifest_id'])
        write(path, data)


def finalize(manifest_id, identifiers):
    for identifier in identifiers:
        path = record_directory(manifest_id, identifier) / 'record.json'
        if not path.is_file():
            continue
        data = json.loads(path.read_text())
        if data.get('status') in ('setup_started', 'started'):
            data.update(status='infra_failed', finished_at=now(),
                        reason_code='job_ended_without_terminal_record', verdict=None)
            write(path, data)


if __name__ == '__main__':
    identifiers = json.loads(os.environ['WPB_SLOTS'])
    if sys.argv[1] == 'start':
        receipt(os.environ['WPB_MODE'], os.environ['WPB_MANIFEST_ID'], identifiers)
    elif sys.argv[1] == 'finish':
        finalize(os.environ['WPB_MANIFEST_ID'], identifiers)
    else:
        raise SystemExit('start or finish required')
