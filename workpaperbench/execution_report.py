"""Inference-free timing and usage analysis of retained native artifacts."""
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import time


def read_json(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 20_000_000:
        raise ValueError('unsafe_execution_artifact')
    return json.loads(path.read_text())


def number(value):
    try:
        if type(value) in (int, float) and math.isfinite(value) and value >= 0:
            return value
    except OverflowError:
        pass
    return None


def counter(value):
    return value if type(value) is int and value >= 0 else None


def total(values):
    return sum(values) if values and all(value is not None for value in values) else None


def elapsed(timing):
    try:
        seconds = (datetime.fromisoformat(timing['finished_at'].replace('Z', '+00:00')) -
                   datetime.fromisoformat(timing['started_at'].replace('Z', '+00:00'))).total_seconds()
        return number(seconds)
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def response_usage(response):
    """Normalize a retained OpenRouter response without reading its content."""
    usage = response.get('usage') or {}
    prompt = counter(usage.get('prompt_tokens'))
    completion = counter(usage.get('completion_tokens'))
    cached = counter((usage.get('prompt_tokens_details') or {}).get('cached_tokens'))
    reasoning = counter((usage.get('completion_tokens_details') or {}).get('reasoning_tokens'))
    identifier = response.get('id')
    reasons = sorted({choice['finish_reason'] for choice in response.get('choices') or []
                      if isinstance(choice.get('finish_reason'), str)})
    return {'response_id': identifier if isinstance(identifier, str) and identifier else None,
        'model': response.get('model'),
        'provider': response.get('provider'), 'prompt_tokens': prompt,
        'completion_tokens': completion, 'cached_tokens': cached,
        'cache_write_tokens': counter((usage.get('prompt_tokens_details') or {}).get('cache_write_tokens')),
        'reasoning_tokens': reasoning, 'total_tokens': total([prompt, completion]),
        'provider_charge': {'amount': number(usage.get('cost')), 'unit': 'OpenRouter credits', 'currency': 'USD',
                            'source': 'OpenRouter response.usage.cost'},
        'finish_reasons': reasons or None,
        'response_replay': (response.get('cache_status') == 'HIT') if 'cache_status' in response else None}


def normalize_responses(observations):
    """Count each identified generation once, retaining conflicting observations."""
    groups = {}
    for index, observation in enumerate(observations):
        row = response_usage(observation)
        key = ('id', row['response_id']) if row['response_id'] else ('unidentified', index)
        groups.setdefault(key, []).append(row)
    responses = []
    for group in groups.values():
        row = {'observation_count': len(group), 'conflicts': {}}
        for field in group[0]:
            if field in ('provider_charge', 'total_tokens'):
                continue
            values = {json.dumps(item[field], sort_keys=True): item[field]
                      for item in group if item[field] is not None}
            row[field] = next(iter(values.values())) if len(values) == 1 else None
            if len(values) > 1:
                row['conflicts'][field] = [values[key] for key in sorted(values)]
        charges = sorted({item['provider_charge']['amount'] for item in group
                          if item['provider_charge']['amount'] is not None})
        row['provider_charge'] = dict(group[0]['provider_charge'],
            amount=charges[0] if len(charges) == 1 else None)
        if len(charges) > 1:
            row['conflicts']['provider_charge'] = charges
        row['total_tokens'] = total([row['prompt_tokens'], row['completion_tokens']])
        responses.append(row)
    return sorted(responses, key=lambda row: json.dumps(row, sort_keys=True))


def summarize_responses(responses):
    identified = [row for row in responses if row['response_id']]
    unidentified = len(responses) - len(identified)
    summary = {'observations': sum(row['observation_count'] for row in responses),
        'identified_generations': len(identified), 'unidentified_observations': unidentified,
        'duplicate_observations': sum(row['observation_count'] - 1 for row in responses),
        'conflicting_generations': sum(bool(row['conflicts']) for row in identified),
        'finish_reason_observed_generations': sum(row['finish_reasons'] is not None for row in identified),
        'length_truncated_generations': sum('length' in (row['finish_reasons'] or []) for row in identified),
        'tokens': {}}
    for field in ('prompt_tokens', 'completion_tokens', 'cached_tokens', 'cache_write_tokens',
                  'reasoning_tokens', 'total_tokens', 'provider_charge'):
        values = [row['provider_charge']['amount'] if field == 'provider_charge' else row[field]
                  for row in identified]
        observed = [value for value in values if value is not None]
        measurement = {'total': total(values) if not unidentified else None,
            'observed_sum': total(observed), 'observed_generations': len(observed),
            'unknown_generations': len(values) - len(observed)}
        if field == 'provider_charge':
            summary[field] = dict(measurement, unit='OpenRouter credits', currency='USD',
                                 source='OpenRouter response.usage.cost')
        else:
            summary['tokens'][field] = measurement
    summary['coverage'] = ('Supplied response records only, without attribution to native trials or new '
        'execution. Unidentified observations remain in response_usage and make complete totals unknown. '
        'Missing failed requests or generations cannot be inferred. Charge observations from other '
        'sources are for reconciliation and must not be added. Cached and reasoning tokens are subsets.')
    return summary


def trial_metrics(path, result=None):
    result = read_json(path) if result is None else result
    context = result.get('agent_result') or {}
    metadata = context.get('metadata') or {}
    request_times = metadata.get('api_request_times_msec')
    requests = ([number(value) for value in request_times] if isinstance(request_times, list) else [])
    phases = {phase + '_seconds': elapsed(result.get(phase) or {})
              for phase in ('environment_setup', 'agent_setup', 'agent_execution', 'verifier')}
    phases.update(wall_seconds=elapsed(result),
                  model_request_seconds=total(requests) / 1000 if total(requests) is not None else None,
                  tool_execution_seconds=None, build_seconds=None)
    # Terminal command durations are requested waits, not measured execution times.
    tokens = {name: counter(context.get(field)) for name, field in (
        ('prompt_tokens', 'n_input_tokens'), ('completion_tokens', 'n_output_tokens'),
        ('cached_tokens', 'n_cache_tokens'))}
    tokens.update(reasoning_tokens=None, total_tokens=total([
        tokens['prompt_tokens'], tokens['completion_tokens']]))
    metrics = {'timing': phases, 'tokens': tokens,
        'native_cost': {'amount': number(context.get('cost_usd')), 'unit': 'USD',
                        'kind': 'reported_or_estimated', 'source': 'agent_result.cost_usd'},
        'actual_charge': {'amount': None, 'unit': 'USD'},
        'request_count': len(requests) if isinstance(request_times, list) else None,
        'request_retries': None,
        'limits': 'Native aggregate usage can omit failed or length-truncated calls followed by recovery. Reasoning is included in completion tokens when reported by the provider. Missing cache or cost fields do not establish zero usage or charges.'}
    if (result.get('config') or {}).get('source_trial'):
        metrics['inherited_model_metrics'] = {'tokens': dict(tokens),
            'native_cost': dict(metrics['native_cost']), 'request_count': metrics['request_count'],
            'model_request_seconds': phases['model_request_seconds']}
        metrics['tokens'] = {key: None for key in tokens}
        metrics['native_cost']['amount'] = None
        metrics['request_count'] = None
        metrics['timing']['model_request_seconds'] = None
    return metrics


def settings(config):
    agent = config.get('agent') or {}
    kwargs = agent.get('kwargs') or {}
    call = kwargs.get('llm_call_kwargs') or {}
    return {'model': agent.get('model_name'),
        'agent': {key: kwargs[key] for key in ('max_turns', 'parser_name', 'enable_summarize',
            'proactive_summarization_threshold', 'use_responses_api', 'reasoning_effort',
            'interleaved_thinking', 'temperature', 'model_info', 'session_id') if key in kwargs},
        'request': {key: call[key] for key in ('max_tokens', 'max_completion_tokens', 'temperature',
            'top_p', 'seed', 'caching', 'timeout', 'num_retries') if key in call},
        'provider_route': (call.get('extra_body') or {}).get('provider'),
        'response_cache_header': (call.get('extra_headers') or {}).get('X-OpenRouter-Cache'),
        'agent_timeout_multiplier': config.get('agent_timeout_multiplier'),
        'environment': {key: value for key, value in (config.get('environment') or {}).items()
                        if key in ('type', 'force_build', 'delete', 'override_cpus', 'override_memory_mb')},
        'evidence': 'Declared native configuration, not proof of provider enforcement'}


def summarize_metrics(metrics, planned=None):
    """Retain coverage rather than treating missing measurements as zero."""
    attempts = max(len(metrics), planned or 0)
    output = {'attempts': attempts, 'recorded_attempts': len(metrics)}
    for group, fields in (
        ('timing', ('environment_setup_seconds', 'agent_setup_seconds', 'agent_execution_seconds',
                    'model_request_seconds', 'tool_execution_seconds', 'verifier_seconds', 'wall_seconds')),
        ('tokens', ('prompt_tokens', 'completion_tokens', 'cached_tokens', 'reasoning_tokens', 'total_tokens'))):
        output[group] = {}
        for field in fields:
            values = [number((row or {}).get(group, {}).get(field)) for row in metrics]
            observed = [value for value in values if value is not None]
            output[group][field] = {'total': total(values) if attempts == len(metrics) else None,
                                    'observed_sum': total(observed),
                                    'observed_attempts': len(observed)}
    return output


def analyze(jobs, destination, usage=None):
    started = time.perf_counter()
    jobs = [Path(path).resolve() for path in jobs]
    if len(set(jobs)) != len(jobs):
        raise ValueError('duplicate_execution_job')
    rows = []
    for job in jobs:
        config = read_json(job / 'config.json')
        result = read_json(job / 'result.json') if (job / 'result.json').exists() else {}
        lock_path = job / 'lock.json'
        lock = read_json(lock_path) if lock_path.exists() else {}
        attempts = []
        for directory in sorted(job.iterdir()):
            if not directory.is_dir() or directory.name.startswith('.'):
                continue
            path = directory / 'result.json'
            if not path.exists():
                if (directory / 'config.json').exists():
                    attempts.append({'trial_name': directory.name, 'status': 'interrupted', 'metrics': None})
                continue
            trial = read_json(path)
            if 'trial_name' not in trial:
                continue
            if trial['trial_name'] != directory.name:
                raise ValueError('execution_trial_identity_changed')
            trajectory_path = directory / 'agent/trajectory.json'
            trajectory = read_json(trajectory_path) if trajectory_path.exists() else {}
            exception = trial.get('exception_info') or {}
            attempts.append({'trial_name': trial['trial_name'], 'task_name': trial.get('task_name'),
                'status': 'interrupted' if not trial.get('finished_at') else ('error' if exception else 'finished'),
                'exception_type': exception.get('exception_type'),
                'rewards': (trial.get('verifier_result') or {}).get('rewards'),
                'source_trial': bool(trial.get('config', {}).get('source_trial')),
                'task_checksum': trial.get('task_checksum'), 'agent_info': trial.get('agent_info'),
                'execution_settings': settings(trial.get('config') or {}),
                'returned_models': sorted({step['model_name'] for step in trajectory.get('steps', [])
                                           if step.get('model_name')}),
                'result_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'metrics': trial_metrics(path, trial)})
        planned = result.get('n_total_trials')
        rows.append({'job': job.name, 'configuration_sha256': hashlib.sha256((job / 'config.json').read_bytes()).hexdigest(),
            'lock_sha256': hashlib.sha256(lock_path.read_bytes()).hexdigest() if lock_path.exists() else None,
            'harbor': lock.get('harbor'), 'concurrent_trials': config.get('n_concurrent_trials'),
            'trial_retry_policy': config.get('retry'), 'planned_trials': planned,
            'unrecorded_slots': max(0, planned - len(attempts)) if type(planned) is int else None,
            'native_stats': result.get('stats'), 'attempts': attempts})
    responses = []
    if usage:
        saved = read_json(Path(usage))
        responses = normalize_responses(saved if isinstance(saved, list) else [saved])
    result = {'report_version': 'execution-1', 'inference': False, 'jobs': rows,
        'summary': summarize_metrics([attempt['metrics'] for row in rows for attempt in row['attempts']],
                                     total([counter(row['planned_trials']) for row in rows])),
        'response_usage': responses,
        'provider_usage_summary': summarize_responses(responses),
        'usage_sha256': hashlib.sha256(Path(usage).read_bytes()).hexdigest() if usage else None,
        'interpretation': 'Read-only analysis, not new attempts or regrading. Responses are a separate usage source and are never added to native aggregates. Cache hits in prompt tokens still generate fresh responses. Full response replay is ineligible for fresh inference. Tool and build time remain unknown when native logs do not measure them.',
        'report_seconds': time.perf_counter() - started}
    with Path(destination).open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result
