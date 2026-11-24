import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

import pytest

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'config/construction-comparison-v15.json'
SPEC = importlib.util.spec_from_file_location('direct_entry', ROOT / 'scripts/validate_direct_harbor.py')
NATIVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NATIVE)


def test_current_and_historical_demos_remain_distinct(tmp_path):
    launcher = tmp_path / 'wpb'
    launcher.write_bytes((ROOT / 'wpb').read_bytes())
    interpreter = tmp_path / '.venv/bin/python'
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text('#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' "$@"\n')
    interpreter.chmod(0o755)
    environment = {**os.environ, 'PYTHONPATH': str(ROOT)}
    current = subprocess.check_output(['sh', str(launcher), 'demo'], cwd=ROOT,
                                      env=environment, text=True)
    module = subprocess.check_output([sys.executable, '-m', 'workpaperbench.current_cli', 'demo'],
                                     cwd=ROOT, text=True)
    historical = subprocess.check_output(['sh', str(launcher), 'legacy', 'demo'], cwd=ROOT,
                                         env=environment, text=True)
    assert current == module
    assert load(ROOT, 'workflow-v15')['manifest_id'] in current
    assert 'Construction track:' in current
    assert 'Historical synthetic formula case:' in historical


@pytest.mark.parametrize('path', [None, 'config/construction-comparison.json'])
def test_comparison_cli_selects_current_or_explicit_historical_recipe(monkeypatch, tmp_path, path):
    arguments = ['validate_direct_harbor', '--harbor', 'unused', '--checkout', '--comparison-recipe']
    if path:
        arguments.append(path)
    arguments += ['--output', str(tmp_path / 'result.json')]
    calls = []
    monkeypatch.setattr(sys, 'argv', arguments)
    monkeypatch.setattr(NATIVE, 'validate', lambda *args: calls.append(args))
    NATIVE.main()
    assert calls[0][2] is True
    assert calls[0][3] == (Path(path) if path else RECIPE)


def test_comparison_rejects_wrong_source_before_launch(tmp_path):
    with pytest.raises(ValueError, match='comparison_recipe_requires_checkout'):
        NATIVE.validate('unused', tmp_path / 'result.json', comparison_recipe=RECIPE)
    with pytest.raises(ValueError, match='comparison_recipe_catalog_mismatch'):
        NATIVE.validate('unused', tmp_path / 'result.json', checkout=True,
                        comparison_recipe=RECIPE, dataset='workflow-v11')
    assert not list(tmp_path.iterdir())


def test_documented_comparison_commands_match_template_without_launching_harbor():
    recipe = json.loads(RECIPE.read_text())
    source, runtime = recipe['task_source'], recipe['runtime']
    manifest = load(ROOT, source['dataset'])
    for field in ('manifest_id', 'scorer_version', 'scorer_sha256', 'sql_worker_sha256'):
        assert source[field] == manifest[field]
    document = (ROOT / 'docs/COMPARISON.md').read_text()
    shell = re.search(r'```bash\n(.*?)\n```', document, re.S)[1]
    capture = shlex.quote('import json,sys; print(json.dumps(sys.argv[1:]))')
    stub = 'harbor() { ' + shlex.quote(sys.executable) + ' -c ' + capture + ' "$@"; }\n'
    result = subprocess.run(['bash', '-eu', '-c', stub + shell], cwd=ROOT,
                            text=True, capture_output=True, check=True)
    commands = [json.loads(line) for line in result.stdout.splitlines()]
    smoke = recipe['stages']['smoke']['tasks_in_order']
    comparison = recipe['stages']['comparison']
    tasks = smoke + [task for task in comparison['tasks_in_order']
                     for _ in range(comparison['attempts_per_task'])]
    assert len(commands) == len(smoke) + comparison['attempts_per_model']
    for command, task in zip(commands, tasks, strict=True):
        def value(flag):
            return command[command.index(flag) + 1]

        assert command[0] == 'run'
        assert value('-p') == source['task_path']
        assert value('-i') == task
        assert value('--env') == runtime['environment']
        assert value('--agent') == runtime['agent']
        assert int(value('--agent-timeout-multiplier')) == runtime['agent_timeout_multiplier']
        assert int(value('--n-concurrent')) == runtime['concurrent_trials']
        assert int(value('--max-retries')) == runtime['trial_retries']
        assert int(value('-k')) == 1
        environment = dict(command[index + 1].split('=', 1)
                           for index, item in enumerate(command) if item == '--ek')
        assert environment == {
            'canonical_root': str(ROOT), 'expected_manifest': source['manifest_id'],
            'expected_task': source['dataset'] + '-' + task}
        options = dict(command[index + 1].split('=', 1)
                       for index, item in enumerate(command) if item == '--ak')
        assert set(options) == set(runtime['agent_kwargs'])
        for key, expected in runtime['agent_kwargs'].items():
            assert (options[key] if isinstance(expected, str) else json.loads(options[key])) == expected
    assert {manifest['tasks'][task]['split'] for task in smoke} == {'development'}
    assert {manifest['tasks'][task]['split'] for task in comparison['tasks_in_order']} == {'evaluation'}
