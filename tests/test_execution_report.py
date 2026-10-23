import json
from pathlib import Path
import subprocess
import sys

import pytest

from workpaperbench.execution_report import (analyze, normalize_responses, response_usage,
    summarize_metrics, summarize_responses, trial_metrics)


def native_job(root):
    job = root / 'job'
    trial = job / 'trial'
    trial.mkdir(parents=True)
    (job / 'config.json').write_text(json.dumps({'n_concurrent_trials': 1, 'retry': {'max_retries': 0}}))
    (job / 'result.json').write_text(json.dumps({'n_total_trials': 3, 'stats': {'n_errored_trials': 1}}))
    (trial / 'result.json').write_text(json.dumps({
        'trial_name': 'trial', 'task_checksum': 'unchanged',
        'started_at': '2026-10-21T00:00:00Z', 'finished_at': '2026-10-21T00:00:10Z',
        'environment_setup': {'started_at': '2026-10-21T00:00:00Z', 'finished_at': '2026-10-21T00:00:02Z'},
        'agent_result': {'n_input_tokens': 100, 'n_cache_tokens': 60, 'n_output_tokens': 20,
                         'cost_usd': 0.1, 'metadata': {'api_request_times_msec': [1000, 2000]}},
        'exception_info': {'exception_type': 'AgentTimeoutError'},
        'verifier_result': {'rewards': {'reward': 0}}}))
    interrupted = job / 'interrupted'
    interrupted.mkdir()
    (interrupted / 'config.json').write_text('{}')
    return job, trial


def test_analysis_preserves_failures_missing_slots_and_unknowns(tmp_path):
    job, trial = native_job(tmp_path)
    original = (trial / 'result.json').read_bytes()
    result = analyze([job], tmp_path / 'analysis.json')
    row = result['jobs'][0]
    assert row['unrecorded_slots'] == 1
    assert result['summary']['attempts'] == 3
    assert result['summary']['recorded_attempts'] == 2
    assert [row['status'] for row in row['attempts']] == ['interrupted', 'error']
    assert row['attempts'][1]['exception_type'] == 'AgentTimeoutError'
    metrics = row['attempts'][1]['metrics']
    assert metrics['timing']['model_request_seconds'] == 3
    assert metrics['timing']['environment_setup_seconds'] == 2
    assert metrics['timing']['wall_seconds'] == 10
    assert metrics['timing']['tool_execution_seconds'] is None
    assert metrics['request_retries'] is None
    assert metrics['tokens']['total_tokens'] == 120
    assert metrics['actual_charge']['amount'] is None
    assert metrics['native_cost']['kind'] == 'reported_or_estimated'
    assert (trial / 'result.json').read_bytes() == original
    with pytest.raises(FileExistsError):
        analyze([job], tmp_path / 'analysis.json')


def test_response_usage_never_adds_cache_or_reasoning_twice():
    row = response_usage({'usage': {'prompt_tokens': 100, 'completion_tokens': 20,
        'prompt_tokens_details': {'cached_tokens': 60},
        'completion_tokens_details': {'reasoning_tokens': 15}, 'cost': 0.003}})
    assert row['total_tokens'] == 120
    assert row['reasoning_tokens'] == 15
    assert row['cached_tokens'] == 60
    assert row['provider_charge']['amount'] == 0.003
    assert response_usage({})['total_tokens'] is None
    assert response_usage({})['provider_charge']['amount'] is None
    assert response_usage({'usage': {'cost': 0}})['provider_charge']['amount'] == 0


def test_partial_metrics_never_imply_complete_totals():
    report = summarize_metrics([{'tokens': {'prompt_tokens': 10}}, None])
    assert report['tokens']['prompt_tokens'] == {'total': None, 'observed_sum': 10, 'observed_attempts': 1}
    assert report['timing']['model_request_seconds']['observed_sum'] is None
    planned = summarize_metrics([{'tokens': {'prompt_tokens': 10}}], planned=2)
    assert planned['tokens']['prompt_tokens']['total'] is None


def test_native_regrade_inherits_usage_without_counting_new_inference(tmp_path):
    _, trial = native_job(tmp_path)
    path = trial / 'result.json'
    data = json.loads(path.read_text())
    data['config'] = {'source_trial': {'path': 'original'}}
    path.write_text(json.dumps(data))
    metrics = trial_metrics(path)
    assert metrics['tokens']['total_tokens'] is None
    assert metrics['native_cost']['amount'] is None
    assert metrics['timing']['model_request_seconds'] is None
    assert metrics['inherited_model_metrics']['tokens']['total_tokens'] == 120
    assert metrics['inherited_model_metrics']['model_request_seconds'] == 3


@pytest.mark.parametrize('value', [None, True, -1, float('nan'), float('inf')])
def test_invalid_native_usage_is_unknown(tmp_path, value):
    path = tmp_path / 'result.json'
    path.write_text(json.dumps({'agent_result': {'n_input_tokens': value}}))
    assert trial_metrics(path)['tokens']['prompt_tokens'] is None


def test_analysis_rejects_duplicate_jobs(tmp_path):
    job, _ = native_job(tmp_path)
    with pytest.raises(ValueError, match='duplicate_execution_job'):
        analyze([job, job], tmp_path / 'analysis.json')


def completion(identifier, prompt, output, cost, cached, reasoning, finish='stop'):
    return {'id': identifier, 'model': 'fixed-model', 'provider': 'fixed-provider',
        'choices': [{'finish_reason': finish}],
        'usage': {'prompt_tokens': prompt, 'completion_tokens': output, 'cost': cost,
            'prompt_tokens_details': {'cached_tokens': cached},
            'completion_tokens_details': {'reasoning_tokens': reasoning}}}


def test_all_generations_include_charged_truncation_recovery_and_deduplicate_observations(tmp_path):
    job, trial = native_job(tmp_path)
    native = json.loads((trial / 'result.json').read_text())
    native['agent_result'].update(n_input_tokens=300, n_output_tokens=50, cost_usd=0.003)
    (trial / 'result.json').write_text(json.dumps(native))
    regrade = job / 'regrade'
    regrade.mkdir()
    native.update(trial_name='regrade', config={'source_trial': {'path': 'trial'}})
    (regrade / 'result.json').write_text(json.dumps(native))
    normal = completion('gen-normal', 100, 20, 0.001, 60, 15)
    truncated = completion('gen-truncated', 200, 16384, 0.01, 150, 16000, 'length')
    recovery = completion('gen-recovery', 200, 30, 0.002, 150, 25)
    # Identical requests can produce distinct, chargeable generations.
    for response in (truncated, recovery):
        response['request'] = {'messages': ['same retained request']}
    observations = [normal, {'id': 'gen-normal'}, truncated, dict(truncated), recovery]
    usage = tmp_path / 'usage.json'
    usage.write_text(json.dumps(observations))
    original = usage.read_bytes()
    result = analyze([job], tmp_path / 'analysis.json', usage)
    summary = result['provider_usage_summary']
    assert summary['observations'] == 5
    assert summary['identified_generations'] == 3
    assert summary['duplicate_observations'] == 2
    assert summary['length_truncated_generations'] == 1
    assert summary['provider_charge']['total'] == pytest.approx(0.013)
    assert summary['provider_charge']['observed_generations'] == 3
    assert summary['tokens']['prompt_tokens']['total'] == 500
    assert summary['tokens']['completion_tokens']['total'] == 16434
    assert summary['tokens']['cached_tokens']['total'] == 360
    assert summary['tokens']['reasoning_tokens']['total'] == 16040
    assert summary['tokens']['total_tokens']['total'] == 16934
    # Provider actuals remain separate from native estimates and inherited regrade usage.
    assert result['summary']['tokens']['prompt_tokens']['observed_sum'] == 300
    assert result['summary']['tokens']['completion_tokens']['observed_sum'] == 50
    inherited = next(row for row in result['jobs'][0]['attempts'] if row.get('source_trial'))
    assert inherited['metrics']['native_cost']['amount'] is None
    assert inherited['metrics']['inherited_model_metrics']['native_cost']['amount'] == 0.003
    assert result['response_usage'] == normalize_responses(list(reversed(observations)))
    assert usage.read_bytes() == original


def test_conflicting_observations_remain_unknown_without_selecting_a_charge():
    first = completion('gen-conflict', 100, 20, 0.003, 60, 15)
    second = completion('gen-conflict', 101, 20, 0.004, 60, 15)
    rows = normalize_responses([first, second])
    assert rows == normalize_responses([second, first])
    assert rows[0]['conflicts'] == {'prompt_tokens': [100, 101], 'provider_charge': [0.003, 0.004]}
    assert rows[0]['prompt_tokens'] is None
    assert rows[0]['provider_charge']['amount'] is None
    summary = summarize_responses(rows)
    assert summary['conflicting_generations'] == 1
    assert summary['tokens']['total_tokens']['total'] is None
    assert summary['tokens']['completion_tokens']['total'] == 20
    assert summary['provider_charge']['total'] is None
    assert summary['provider_charge']['unknown_generations'] == 1


def test_missing_identity_or_usage_preserves_coverage_and_unknowns():
    known = completion('gen-known', 100, 20, 0, 60, 15)
    anonymous = completion(None, 200, 30, 0.002, None, None)
    rows = normalize_responses([known, {'id': 'gen-missing-usage'}, anonymous, anonymous])
    summary = summarize_responses(rows)
    assert summary['identified_generations'] == 2
    assert summary['unidentified_observations'] == 2
    assert summary['duplicate_observations'] == 0
    assert summary['tokens']['prompt_tokens'] == {
        'total': None, 'observed_sum': 100, 'observed_generations': 1, 'unknown_generations': 1}
    assert summary['provider_charge']['total'] is None
    assert summary['provider_charge']['observed_sum'] == 0
    assert sum(row['response_id'] is None for row in rows) == 2


def test_analysis_cli_needs_no_native_runtime_or_key(tmp_path):
    job, _ = native_job(tmp_path)
    output = tmp_path / 'analysis.json'
    result = subprocess.run([sys.executable, '-m', 'workpaperbench.current_cli', 'analyze',
        '--jobs', str(job), '--output', str(output)], cwd=Path(__file__).parents[1],
        env={'PATH': '/usr/bin:/bin'}, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text())['inference'] is False
