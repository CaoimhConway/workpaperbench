"""Assemble eight task-local native packages from committed small source records."""
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

ROOT = Path(__file__).resolve().parent.parent


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def database(path, tables):
    path.unlink(missing_ok=True)
    db = sqlite3.connect(path)
    for name, table in tables.items():
        db.execute(table['schema'])
        if table['rows']:
            marks = ','.join('?' for _ in table['rows'][0])
            db.executemany(f'INSERT INTO {name} VALUES ({marks})', table['rows'])
    db.commit()
    db.execute('VACUUM')
    db.close()


def build(identifier):
    definition = json.loads((ROOT / 'sources' / f'{identifier}.json').read_text())
    task = ROOT / 'tasks' / identifier
    environment = task / 'environment'
    tests = task / 'tests'
    solution = task / 'solution'
    for directory in (environment, tests, solution):
        directory.mkdir(parents=True, exist_ok=True)
    database(environment / 'data.sqlite', definition['tables'])
    database(tests / 'changed.sqlite', definition['changed_tables'])
    shutil.copyfile(environment / 'data.sqlite', tests / 'data.sqlite')
    shutil.copyfile(ROOT / 'config/schema.json', environment / 'schema.json')
    shutil.copyfile(ROOT / 'config/schema.json', tests / 'schema.json')
    shutil.copyfile(ROOT / 'scripts/check_answer.py', environment / 'check_answer.py')
    shutil.copyfile(ROOT / 'scripts/verify.py', tests / 'verify.py')
    shutil.copytree(ROOT / 'workpaperbench', tests / 'workpaperbench', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', 'cli.py'))
    evidence = definition['evidence']
    for record in evidence:
        record['content_sha256'] = hashlib.sha256(record['text'].encode()).hexdigest()
        record['derived_sha256'] = hashlib.sha256(json.dumps(definition['tables'], sort_keys=True).encode()).hexdigest()
    write_json(environment / 'evidence.json', evidence)
    (environment / 'sources.md').write_text(definition['context'] + '\n')
    shutil.copyfile(environment / 'evidence.json', tests / 'evidence.json')
    shutil.copyfile(environment / 'sources.md', tests / 'sources.md')
    common = '\n\nInputs are in /workspace: data.sqlite, evidence.json, sources.md, schema.json and check_answer.py. '
    common += 'Publish one answer.json at /logs/artifacts/answer.json, using the shared schema. '
    common += 'Provide only the requested claim IDs, canonical units and one conclusion if requested. '
    common += 'For each answered claim include a single read-only SQLite statement returning one numeric column named value. '
    common += 'Queries are replayed on pristine data and a declared schema-compatible synthetic changed-data control. '
    common += 'The control varies amounts or observations without changing metric definitions, covered populations or source eligibility rules. '
    common += 'Evidence lists must identify the supporting records and definitions for each claim. '
    common += 'If an input is unavailable, use insufficient_evidence with null value and SQL and a reason code. '
    common += 'Values must be finite. Numerical tolerance is 0.000001 in the requested unit. '
    common += 'The common checker verifies structure only: python /workspace/check_answer.py /logs/artifacts/answer.json. '
    common += 'Do not modify the supplied inputs. Do not leave other files in /logs/artifacts. There is no open-web research during solving.'
    (task / 'instruction.md').write_text(definition['instruction'] + common + '\n')
    write_json(tests / 'reference.json', definition['reference'])
    (solution / 'solve.sh').write_text('#!/bin/bash\nset -euo pipefail\ncat > /logs/artifacts/answer.json <<\'ANSWER\'\n' + json.dumps(definition['reference'], indent=2) + '\nANSWER\n')
    (tests / 'test.sh').write_text('#!/bin/bash\nset -euo pipefail\npython /tests/verify.py\n')
    gold = definition['gold']
    gold['task_id'] = identifier
    gold['hashes'] = {name: hashlib.sha256((tests / name).read_bytes()).hexdigest()
                      for name in ('data.sqlite', 'changed.sqlite', 'schema.json', 'evidence.json', 'sources.md')}
    write_json(tests / 'gold.json', gold)
    runtime = json.loads((ROOT / 'config/runtime.json').read_text())
    (environment / 'Dockerfile').write_text('FROM ' + runtime['base_image'] + '\n'
        'WORKDIR /workspace\n'
        'RUN apt-get update && apt-get install -y --no-install-recommends bash curl git ca-certificates procps iproute2 && rm -rf /var/lib/apt/lists/*\n'
        'RUN pip install --no-cache-dir jsonschema==4.26.0\n'
        'COPY data.sqlite evidence.json sources.md schema.json check_answer.py /workspace/\n')
    (tests / 'Dockerfile').write_text('FROM ' + runtime['base_image'] + '\n'
        'RUN pip install --no-cache-dir jsonschema==4.26.0\n'
        'COPY . /tests/\n')
    (tests / 'docker-compose.yaml').write_text('services:\n  main:\n    network_mode: none\n')
    (task / 'task.toml').write_text(runtime['task_toml'].replace('{task_id}', identifier))
    return identifier


if __name__ == '__main__':
    for path in sorted((ROOT / 'sources').glob('wp*.json')):
        print(build(path.stem))
