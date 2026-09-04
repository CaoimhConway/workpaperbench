"""Build the real-v1 native packages from retained source bytes, offline."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import re
import sqlite3
from html.parser import HTMLParser

from build_tasks import database, write_json

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / 'datasets/real-v1'


class FilingRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.row = []

    def handle_data(self, data):
        if self.row is not None:
            self.row.append(data)

    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None:
            self.rows.append(' '.join(self.row))
            self.row = None


def filing_numbers(name, label, expected):
    path = DATASET / 'captures' / (name + '-filing-tables.html')
    metadata = json.loads(path.with_suffix('.json').read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != metadata['retained_extract_sha256']:
        raise ValueError('Changed original filing extract')
    parser = FilingRows()
    parser.feed(path.read_text())
    candidates = []
    for row in parser.rows:
        if label in row:
            values = [int(n.replace(',', '')) for n in re.findall(r'(?<![a-zA-Z0-9.])[0-9]+(?:,[0-9]{3})*(?![a-zA-Z0-9.])', row)]
            candidates.append(values)
    if list(expected) not in candidates:
        raise ValueError('Filing values or order differ from accession table')
    return list(expected), metadata


def legacy_definition(identifier):
    definition = json.loads((ROOT / 'sources' / (identifier + '.json')).read_text())
    definition['task_id'] = 'real-v1-' + identifier
    definition['reference']['task_id'] = definition['task_id']
    definition['control_origin'] = 'deliberately_perturbed_real_data' if identifier in ('wp01', 'wp07') else 'fully_synthetic_data'
    definition['previously_exposed'] = True
    if identifier == 'wp01':
        values, metadata = filing_numbers('tesla', 'Research and development', (1074, 943, 2225, 1714))
        rows = definition['tables']['expenses']['rows']
        for row, value in zip(rows, (values[0], values[2], values[1], values[3])):
            row[4] = value
    elif identifier == 'wp07':
        revenue, metadata = filing_numbers('apple', 'Services', (23867, 20907, 46984, 41673))
        profit, _ = filing_numbers('apple', 'Services', (17809, 14842, 34646, 29551))
        for row, r, g in zip(definition['tables']['services']['rows'], (revenue[0], revenue[2], revenue[1], revenue[3]), (profit[0], profit[2], profit[1], profit[3])):
            row[3:5] = [r, g]
    if identifier in ('wp01', 'wp07'):
        definition['origin'] = 'deterministic_source_derived'
        for record in definition['evidence']:
            record['retrieved_at'] = metadata['retrieved_at']
            record['capture_sha256'] = metadata['retained_extract_sha256']
        definition['context'] += '\n\nObserved accession-specific factual table extract, deterministically normalized. This is a previously exposed regression question, not a newly unseen evaluation.'
    if identifier == 'wp02':
        for key in ('tables', 'changed_tables'):
            rows = definition[key]['events']['rows']
            rows[4][4] = rows[0][4]
        definition['reference']['answers'][0]['value'] = 1000
        definition['gold']['answers']['transfer_total'].update(value=1000, changed_value=1220)
        definition['previously_exposed'] = 'Revised previously exposed diagnostic with new equal-amount events'
        definition['context'] += '\n\nThis new synthetic control includes equal amounts on different legitimate event identities. It is not observed chain data.'
    return definition


def package(identifier, definition, destination):
    task_id = definition['task_id']
    task = destination / 'tasks' / identifier
    environment, tests, solution = [task / name for name in ('environment', 'tests', 'solution')]
    for directory in (environment, tests, solution):
        directory.mkdir(parents=True, exist_ok=True)
    database(environment / 'data.sqlite', definition['tables'])
    database(tests / 'changed.sqlite', definition['changed_tables'])
    if (DATASET / 'manifest.json').is_file():
        for path in (environment / 'data.sqlite', tests / 'changed.sqlite'):
            retained = DATASET / path.relative_to(destination)
            if sqlite_contents(retained) != sqlite_contents(path):
                raise ValueError('Source-derived table reconstruction mismatch: ' + str(retained.relative_to(ROOT)))
            if retained.read_bytes() != path.read_bytes():
                old, rebuilt = retained.read_bytes(), path.read_bytes()
                offset = next((i for i, pair in enumerate(zip(old, rebuilt)) if pair[0] != pair[1]), min(len(old), len(rebuilt)))
                print(f'SQLite layout differs at byte {offset}: ' + str(retained.relative_to(ROOT)) + f', lengths {len(old)}/{len(rebuilt)}. Schema and complete typed rows match. Retaining frozen SQLite bytes.')
            shutil.copyfile(retained, path)
    shutil.copyfile(environment / 'data.sqlite', tests / 'data.sqlite')
    for directory in (environment, tests):
        shutil.copyfile(DATASET / 'schema.json', directory / 'schema.json')
    shutil.copyfile(ROOT / 'scripts/check_answer.py', environment / 'check_answer.py')
    shutil.copyfile(ROOT / 'scripts/verify.py', tests / 'verify.py')
    shutil.copytree(ROOT / 'workpaperbench', tests / 'workpaperbench',
                    ignore=shutil.ignore_patterns('__pycache__', 'cli.py', 'real_report.py'))
    evidence = copy.deepcopy(definition['evidence'])
    for record in evidence:
        record['content_sha256'] = hashlib.sha256(record['text'].encode()).hexdigest()
        record['derived_sha256'] = hashlib.sha256(json.dumps(definition['tables'], sort_keys=True).encode()).hexdigest()
    write_json(environment / 'evidence.json', evidence)
    (environment / 'sources.md').write_text(definition['context'].rstrip() + '\n')
    for name in ('evidence.json', 'sources.md'):
        shutil.copyfile(environment / name, tests / name)
    common = f'\n\nTask identifier: {task_id}. Inputs are in /workspace: data.sqlite, evidence.json, sources.md, schema.json and check_answer.py. '
    common += 'Publish only answer.json at /logs/artifacts/answer.json using the shared schema. '
    common += 'Provide exactly the requested claim IDs, units and one conclusion if requested. '
    common += 'For each answered claim include a read-only deterministic SQLite statement returning one numeric column named value. '
    common += 'SQL is replayed against pristine data and an explicitly synthetic schema-compatible changed-data control. '
    common += 'The control changes numerical observations without changing metric definitions or source eligibility. '
    common += 'The evidence contract is per claim: cite the record IDs supporting that calculation and its metric definition. '
    common += 'A combined record describing both is an equivalent evidence path. A conclusion cites the supporting calculation or the relevant scope evidence. '
    common += 'Do not cite unrelated records. There is no hidden citation repetition rule beyond this declared per-claim contract. '
    common += 'Unavailable inputs use insufficient_evidence with null value and SQL and a schema reason code. '
    common += 'Numerical tolerance is 0.000001 in the requested unit. All values must be finite. '
    common += 'Use the common structure checker: python /workspace/check_answer.py /logs/artifacts/answer.json. '
    common += 'Do not modify inputs. There is no network acquisition during solving.'
    (task / 'instruction.md').write_text(definition['instruction'] + common + '\n')
    write_json(tests / 'reference.json', definition['reference'])
    (solution / 'solve.sh').write_text("#!/bin/bash\nset -euo pipefail\ncat > /logs/artifacts/answer.json <<'ANSWER'\n" + json.dumps(definition['reference'], indent=2) + '\nANSWER\n')
    (tests / 'test.sh').write_text('#!/bin/bash\nset -euo pipefail\npython /tests/verify.py\n')
    gold = copy.deepcopy(definition['gold'])
    gold['task_id'] = task_id
    gold['hashes'] = {name: hashlib.sha256((tests / name).read_bytes()).hexdigest()
                      for name in ('data.sqlite', 'changed.sqlite', 'schema.json', 'evidence.json', 'sources.md')}
    write_json(tests / 'gold.json', gold)
    for name in ('environment/Dockerfile', 'tests/Dockerfile', 'tests/docker-compose.yaml'):
        shutil.copyfile(ROOT / 'tasks/wp01' / name, task / name)
    runtime = json.loads((ROOT / 'config/runtime.json').read_text())
    (task / 'task.toml').write_text(runtime['task_toml'].replace('{task_id}', task_id))
    write_json(destination / 'sources' / (identifier + '.json'), definition)


def definitions():
    from real_definitions import crypto_definitions
    return {**{name: legacy_definition(name) for name in ('wp01', 'wp02', 'wp05', 'wp07')}, **crypto_definitions()}


def sqlite_contents(path):
    """Compare trusted generated tables without relying on SQLite page layout."""
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        schema = db.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name').fetchall()
        tables = {}
        for kind, name, _, _ in schema:
            if kind != 'table':
                continue
            quoted = '"' + name.replace('"', '""') + '"'
            rows = db.execute('SELECT * FROM ' + quoted + ' ORDER BY rowid').fetchall()
            tables[name] = [[(type(value).__name__, value) for value in row] for row in rows]
        return schema, tables


def build(check=False):
    manifest_path = DATASET / 'manifest.json'
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        from operations_review import reviewed_hashes
        for name, expected in reviewed_hashes(manifest, ROOT).items():
            path = ROOT / name
            if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError('Frozen input hash mismatch: ' + name)
    with tempfile.TemporaryDirectory() as temporary:
        staged = Path(temporary)
        (staged / 'sources').mkdir()
        for identifier, definition in sorted(definitions().items()):
            package(identifier, definition, staged)
        for path in sorted(staged.rglob('*')):
            if not path.is_file():
                continue
            target = DATASET / path.relative_to(staged)
            if check or (DATASET / 'manifest.json').is_file():
                if not target.is_file() or target.read_bytes() != path.read_bytes():
                    expected = target.read_bytes() if target.is_file() else b''
                    actual = path.read_bytes()
                    offset = next((i for i, pair in enumerate(zip(expected, actual)) if pair[0] != pair[1]), min(len(expected), len(actual)))
                    raise ValueError('Offline reconstruction mismatch: ' + str(target.relative_to(ROOT)) + f' at byte {offset}, expected {expected[offset:offset+8].hex()}, rebuilt {actual[offset:offset+8].hex()}, lengths {len(expected)}/{len(actual)}')
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print('Eight real-v1 packages reconstructed offline' + (' with exact non-SQLite bytes, complete typed table equality and frozen input hashes' if check else ''))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
