import json
from pathlib import Path
import subprocess
import sys

import pytest

from workpaperbench.execution_report import analyze, response_usage, summarize_metrics, trial_metrics


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


def test_analysis_rejects_duplicate_jobs_and_response_ids(tmp_path):
    job, _ = native_job(tmp_path)
    with pytest.raises(ValueError, match='duplicate_execution_job'):
        analyze([job, job], tmp_path / 'analysis.json')
    usage = tmp_path / 'usage.json'
    usage.write_text(json.dumps([{'id': 'same'}, {'id': 'same'}]))
    with pytest.raises(ValueError, match='duplicate_response_usage'):
        analyze([job], tmp_path / 'analysis.json', usage)


def test_analysis_cli_needs_no_native_runtime_or_key(tmp_path):
    job, _ = native_job(tmp_path)
    output = tmp_path / 'analysis.json'
    result = subprocess.run([sys.executable, '-m', 'workpaperbench.current_cli', 'analyze',
        '--jobs', str(job), '--output', str(output)], cwd=Path(__file__).parents[1],
        env={'PATH': '/usr/bin:/bin'}, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text())['inference'] is False
