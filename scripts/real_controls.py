"""Hosted native controls for the source-backed real-v1 suite."""
import copy
import json
import os
from pathlib import Path

from integration import ROOT, RAW, OUTPUT, control, native


def main():
    if os.environ.get('RUNNER_OS') != 'Linux' or os.environ.get('GITHUB_ACTIONS') != 'true':
        raise SystemExit('Native verification runs only on hosted Linux Actions')
    if any(k in os.environ for k in ('OPENROUTER_API_KEY', 'ARTEMIS_API_KEY', 'GH_TOKEN', 'GITHUB_TOKEN')):
        raise SystemExit('No inference, acquisition or GitHub key belongs in verifier controls')
    RAW.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    results = []
    task_root = ROOT / 'datasets/real-v1/tasks'
    boundaries = """test ! -e /tests/gold.json
test ! -e /var/run/docker.sock
test ! -d /workspace/.git
test ! -e /workspace/prior-marker
touch /workspace/prior-marker
python - <<'CHECK'
import os
from urllib.request import urlopen
assert not any(k in os.environ for k in ('OPENROUTER_API_KEY', 'ARTEMIS_API_KEY', 'GH_TOKEN', 'GITHUB_TOKEN'))
with urlopen('https://openrouter.ai/api/v1/models', timeout=20) as response:
    assert response.status == 200
for url in ('https://example.com', 'https://api.llama.fi'):
    try:
        urlopen(url, timeout=3)
    except Exception:
        continue
    raise AssertionError('Unexpected candidate network access')
CHECK
"""
    for task in sorted(task_root.glob('wp*')):
        ref = json.loads((task / 'tests/reference.json').read_text())
        name = 'real-v1-' + task.name
        results.append(native(control(task, name + '-reference', ref, boundaries), name + '-reference', True))
        results.append(native(task, name + '-empty', False, 'nop'))
        alternate = copy.deepcopy(ref)
        for claim in alternate['answers']:
            if claim['sql']:
                claim['sql'] = 'WITH calculated AS (' + claim['sql'] + ') SELECT value FROM calculated'
        results.append(native(control(task, name + '-alternative', alternate), name + '-alternative', True))
        constant = copy.deepcopy(ref)
        claim = next(c for c in constant['answers'] if c['status'] == 'answered')
        claim['sql'] = 'SELECT ' + str(claim['value']) + ' AS value'
        results.append(native(control(task, name + '-constant', constant), name + '-constant', False))
    task = task_root / 'wp02'
    ref = json.loads((task / 'tests/reference.json').read_text())
    for label, sql, expected in (
        ('amount-distinct', "SELECT SUM(DISTINCT amount_units) AS value FROM events WHERE event_kind='transfer'", False),
        ('event-distinct', "SELECT SUM(amount_units) AS value FROM (SELECT DISTINCT event_id,amount_units FROM events WHERE event_kind='transfer')", True),
        ('event-window', "WITH e AS (SELECT amount_units,ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY export_row) n FROM events WHERE event_kind='transfer') SELECT SUM(amount_units) AS value FROM e WHERE n=1", True),
    ):
        answer = copy.deepcopy(ref)
        answer['answers'][0]['sql'] = sql
        name = 'real-v1-' + label
        result = native(control(task, name, answer), name, expected)
        if not expected:
            assert result['verdict']['checks']['numerical'] is True
            assert result['verdict']['checks']['replay'] is False
        results.append(result)
    for label, extra, answer, expected in (
        ('tampered-input', 'rm /workspace/data.sqlite\nprintf broken > /workspace/data.sqlite\n', ref, True),
        ('extra-artifact', 'printf unexpected > /logs/artifacts/extra.txt\n', ref, False),
        ('extra-claim', '', {**ref, 'answers': ref['answers'] + [{**ref['answers'][0], 'id': 'unrequested'}]}, False),
    ):
        name = 'real-v1-' + label
        item = native(control(task, name, answer, extra), name, expected)
        if label == 'extra-claim':
            assert item['verdict']['checks']['replay'] is None
            assert item['verdict']['checks']['numerical'] is True
        results.append(item)
    for label, sql in (
        ('forbidden-sql', "ATTACH DATABASE '/tmp/escape' AS x"),
        ('bounded-sql', 'WITH RECURSIVE t(n) AS (VALUES(1) UNION ALL SELECT n+1 FROM t) SELECT SUM(n) AS value FROM t'),
    ):
        answer = copy.deepcopy(ref)
        answer['answers'][0]['sql'] = sql
        name = 'real-v1-' + label
        results.append(native(control(task, name, answer), name, False))
    output = {'dataset_id': 'real-v1', 'run_id': os.environ['GITHUB_RUN_ID'],
              'commit_sha': os.environ['GITHUB_SHA'], 'controls': results}
    (OUTPUT / 'real-v1-controls.json').write_text(json.dumps(output, indent=2) + '\n')


if __name__ == '__main__':
    main()
