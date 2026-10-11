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
    track = row.get('evaluation_track', 'maintenance')
    if track not in ('construction', 'maintenance'):
        raise ValueError('report_unknown_evaluation_track')
    identity = ('manifest_id', 'task_id', 'task_sha256', 'scorer_sha256')
    matches = [item for item in baselines if all(item.get(key) == row.get(key) for key in identity)]
    if len(matches) > 1:
        raise ValueError('report_duplicate_baseline')
    baseline = matches[0] if matches and track == 'maintenance' else None
    verdict = row.get('verdict', {})
    checks = verdict.get('checks', {})
    infrastructure = row.get('status') in ('infrastructure_failed', 'cancelled', 'started')
    assessed = not infrastructure and checks.get('delivery') is True
    tables = verdict.get('details', {}).get('tables', {}) if assessed else {}
    initial = baseline['tables'] if baseline else {}
    requested = set(row.get('requested_tables', initial or tables))
    if tables and requested and set(tables) != requested:
        raise ValueError('report_table_sets_differ')
    changes = {}
    outcomes = {}
    for name in sorted(requested | set(initial) | set(tables)):
        after = tables.get(name, {})
        outcomes[name] = {
            scope: {True: 'Correct', False: 'Incorrect', None: 'Unassessed'}[table_state(after, controls)]
            for scope, controls in (('original_inputs', False), ('original_and_controls', True))
        }
        changes[name] = {
            **(change(initial[name], after) if baseline else {
                'original_inputs': 'Unassessed', 'original_and_controls': 'Unassessed'}),
            'original_error': after.get('original_error'),
            'failed_controls': {key: after.get('control_errors', {}).get(key, 'mismatch')
                                for key, passed in after.get('controls', {}).items() if passed is False},
        }
        if track == 'construction':
            changes[name].pop('original_inputs')
            changes[name].pop('original_and_controls')
    counts = {scope: dict(Counter(item[scope] for item in changes.values()))
              for scope in ('original_inputs', 'original_and_controls')} if track == 'maintenance' else None
    opportunities = {scope: {
        'initially_incorrect': sum(table_state(item, controls) is False for item in initial.values()),
        'initially_correct': sum(table_state(item, controls) is True for item in initial.values()),
    } for scope, controls in (('original_inputs', False), ('original_and_controls', True))} if baseline else None
    reasoning = dimension(checks.get('numerical_tables'), checks.get('claim_verdicts'))
    if 'numerical_tables' not in checks and 'claim_verdicts' not in checks:
        reasoning = dimension(checks.get('financial_answer'))
    return {
        'attempt_id': row['attempt_id'], 'task_id': row.get('task_id'),
        'evaluation_track': track,
        'condition': 'continued' if row.get('continuation') else 'fresh',
        'source_kind': row.get('source_kind', 'model_attempt' if row.get('inference') else 'artifact_verification'),
        'baseline_matched': baseline is not None,
        'baseline_note': ('No starting SQL is supplied. Repair and preservation are not applicable.'
                          if track == 'construction' else
                          'Same task, scorer and control inputs on both sides' if baseline else
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
        'tables': changes,
        'table_outcomes': outcomes,
        'outcome_counts': {scope: dict(Counter(item[scope] for item in outcomes.values()))
                           for scope in ('original_inputs', 'original_and_controls')},
        'transition_counts': counts,
        'opportunities': opportunities,
    }


def aggregate(rows, diagnostics):
    """Count observed outcomes without claiming statistical independence or known cost."""
    tasks = Counter(row.get('task_id', 'unknown') for row in rows)
    costs = [row.get('external_service_spend_usd') for row in rows]
    measured_cost = all(type(value) in (int, float) and value >= 0 for value in costs)
    return {
        'attempts': len(rows),
        'distinct_tasks': len(tasks),
        'repeated_tasks': {key: count for key, count in tasks.items() if count > 1},
        'task_splits': dict(Counter(row.get('task_split', 'unspecified') for row in rows)),
        'model_attempts_by_split': dict(Counter(row.get('task_split', 'unspecified')
                                               for row in rows if row['inference'])),
        'fully_correct_workpapers': sum(row.get('verdict', {}).get('complete') is True
                                       and item['failure_dimensions']['infrastructure'] == 'pass'
                                       for row, item in zip(rows, diagnostics)),
        'infrastructure_failures': sum(item['failure_dimensions']['infrastructure'] == 'fail'
                                       for item in diagnostics),
        'table_outcomes': {scope: dict(sum((Counter(item['outcome_counts'][scope])
                                          for item in diagnostics), Counter()))
                          for scope in ('original_inputs', 'original_and_controls')},
        'external_service_spend_usd': sum(costs) if measured_cost else None,
        'cost_evidence': 'Sum of recorded costs' if measured_cost else 'Not measured for every attempt',
    }
