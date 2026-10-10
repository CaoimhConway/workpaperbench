"""Interpret table changes without turning missing evidence into a model error."""
from collections import Counter


def transition(before, after):
    if type(before) is not bool or type(after) is not bool:
        return 'Unassessed'
    return {(False, True): 'Repair', (True, True): 'Preservation',
            (True, False): 'Regression', (False, False): 'Unrepaired'}[before, after]


def table_state(table, controls=False):
    values = [table.get('original')]
    if controls:
        values += list(table.get('controls', {}).values())
    return all(values) if all(type(value) is bool for value in values) else None


def change(before, after):
    if after and set(before['controls']) != set(after['controls']):
        raise ValueError('report_control_sets_differ')
    return {
        'original_inputs': transition(table_state(before), table_state(after)),
        'original_and_controls': transition(table_state(before, True), table_state(after, True)),
    }


def dimension(*values):
    if any(value is False for value in values):
        return 'fail'
    return 'pass' if values and all(value is True for value in values) else 'unassessed'


def summarize(row, baselines):
    identity = ('manifest_id', 'task_id', 'task_sha256', 'scorer_sha256')
    matches = [item for item in baselines if all(item.get(key) == row.get(key) for key in identity)]
    if len(matches) > 1:
        raise ValueError('report_duplicate_baseline')
    baseline = matches[0] if matches else None
    verdict = row.get('verdict', {})
    checks = verdict.get('checks', {})
    infrastructure = row.get('status') in ('infrastructure_failed', 'cancelled', 'started')
    assessed = not infrastructure and checks.get('delivery') is True
    tables = verdict.get('details', {}).get('tables', {}) if assessed else {}
    initial = baseline['tables'] if baseline else {}
    if baseline and tables and set(tables) != set(initial):
        raise ValueError('report_table_sets_differ')
    changes = {}
    for name in sorted(set(initial) | set(tables)):
        after = tables.get(name, {})
        changes[name] = {
            **(change(initial[name], after) if baseline else {
                'original_inputs': 'Unassessed', 'original_and_controls': 'Unassessed'}),
            'original_error': after.get('original_error'),
            'failed_controls': {key: after.get('control_errors', {}).get(key, 'mismatch')
                                for key, passed in after.get('controls', {}).items() if passed is False},
        }
    counts = {scope: dict(Counter(item[scope] for item in changes.values()))
              for scope in ('original_inputs', 'original_and_controls')}
    opportunities = {scope: {
        'initially_incorrect': sum(table_state(item, controls) is False for item in initial.values()),
        'initially_correct': sum(table_state(item, controls) is True for item in initial.values()),
    } for scope, controls in (('original_inputs', False), ('original_and_controls', True))} if baseline else None
    reasoning = dimension(checks.get('numerical_tables'), checks.get('claim_verdicts'))
    if 'numerical_tables' not in checks and 'claim_verdicts' not in checks:
        reasoning = dimension(checks.get('financial_answer'))
    return {
        'attempt_id': row['attempt_id'], 'task_id': row.get('task_id'),
        'condition': 'continued' if row.get('continuation') else 'fresh',
        'source_kind': row.get('source_kind', 'model_attempt' if row.get('inference') else 'artifact_verification'),
        'baseline_matched': baseline is not None,
        'baseline_note': ('Same task, scorer and control inputs on both sides' if baseline else
                          'No matching starting-SQL receipt. Changes remain unassessed'),
        'failure_dimensions': {
            'reasoning_or_calculation': 'unassessed' if infrastructure else reasoning,
            'evidence': 'unassessed' if infrastructure else dimension(checks.get('evidence')),
            'robustness': 'unassessed' if infrastructure else dimension(checks.get('robustness')),
            'delivery': 'unassessed' if infrastructure else dimension(checks.get('delivery')),
            'infrastructure': 'fail' if infrastructure else ('pass' if row.get('status') in (
                'verified', 'candidate_failed') else 'unassessed'),
        },
        'candidate_error_type': row.get('candidate_error_type'),
        'tables': changes, 'transition_counts': counts, 'opportunities': opportunities,
    }
