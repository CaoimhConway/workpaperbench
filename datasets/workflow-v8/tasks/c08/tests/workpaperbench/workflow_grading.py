"""Independent financial, evidence, preservation and delivery diagnostics."""
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

from jsonschema import Draft202012Validator
from .grading import close, digest, parse

SCORER_VERSION = 'workflow-1.2.0'

# Source locators use namespace:s<digits>. Retain identifier-like prefixes and
# suffixes, including wrong case, so malformed IDs cannot become valid citations.
# Other colon notation, such as FY2025:Q2 or Definition:margin, is ordinary prose.
CITATION = re.compile(r'(?<![A-Za-z0-9_-])[A-Za-z0-9_][A-Za-z0-9_-]*:[sS][0-9][A-Za-z0-9_-]*')


def read_file(path, maximum):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('artifact_symlink')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
            raise ValueError('artifact_type_or_size')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(maximum + 1)
        if len(raw) > maximum:
            raise ValueError('artifact_size')
        return raw
    finally:
        os.close(fd)


def load_artifacts(directory, gold, schema):
    directory = Path(directory)
    if directory.is_symlink() or any(parent.is_symlink() for parent in directory.parents):
        raise ValueError('artifact_directory_symlink')
    answer = parse(read_file(directory / 'answer.json', 65536))
    Draft202012Validator(schema).validate(answer)
    if answer['task_id'] != gold['task_id']:
        raise ValueError('task_identity')
    files = {}
    for table in answer['tables']:
        if table['id'] in files or not re.fullmatch(r'[a-z][a-z0-9_]{0,40}\.sql', table['file']):
            raise ValueError('duplicate_table_or_unsafe_file')
        files[table['id']] = table['file']
    claims = [claim['id'] for claim in answer['claims']]
    if (set(files) != set(gold['tables']) or len(claims) != len(set(claims))
            or set(claims) != set(gold['claims']) or len(set(files.values())) != len(files)):
        raise ValueError('requested_output_set')
    if sorted(path.name for path in directory.iterdir()) != sorted(['answer.json', *files.values()]):
        raise ValueError('unexpected_artifacts')
    sql = {identifier: read_file(directory / name, 16384).decode('utf-8') for identifier, name in files.items()}
    return answer, sql


def replay(sql, db):
    worker = Path(__file__).with_name('workflow_sql_worker.py').resolve()
    try:
        result = subprocess.run([sys.executable, '-I', '-S', str(worker)],
            input=json.dumps({'sql': sql, 'db': str(Path(db).resolve())}), text=True,
            capture_output=True, timeout=2.5, cwd=worker.parent,
            env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'})
        if result.returncode or len(result.stdout.encode()) > 65536:
            return None
        value = parse(result.stdout)
        return value if set(value) == {'columns', 'rows'} else None
    except (ValueError, OSError, subprocess.TimeoutExpired):
        return None


def comparison_error(actual, spec, expected):
    if actual is None:
        return 'sql_execution'
    if set(actual['columns']) != set(spec['columns']):
        return 'columns'
    columns = list(spec['columns'])
    if len(actual['columns']) != len(columns):
        return 'columns'
    if len(actual['rows']) != len(expected):
        return 'rows'
    def index(rows):
        indexed = {}
        for row in rows:
            if len(row) != len(columns):
                return None
            key = tuple(row[columns.index(name)] for name in spec['keys'])
            if key in indexed:
                return None
            indexed[key] = row
        return indexed
    rows = []
    for row in actual['rows']:
        if len(row) != len(columns):
            return 'rows'
        reordered = []
        for name in columns:
            value = row[actual['columns'].index(name)]
            column = spec['columns'][name]
            if column['type'] == 'text' and isinstance(value, str):
                value = column.get('aliases', {}).get(value, value)
            reordered.append(value)
        rows.append(reordered)
    given, wanted = index(rows), index(expected)
    if given is None or wanted is None or set(given) != set(wanted):
        return 'keys'
    for key, row in given.items():
        for value, target, column in zip(row, wanted[key], spec['columns'].values()):
            if column['type'] == 'text':
                if not isinstance(value, str) or value != target:
                    return 'text'
            elif column['type'] == 'integer':
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value != target:
                    return 'numeric'
            elif not close(value, target, column['tolerance']):
                return 'numeric'
    return None


def compare(actual, spec, expected):
    return comparison_error(actual, spec, expected) is None


def supported(given, options, context):
    supplied = {identifier for item in given for identifier in CITATION.findall(item)}
    return supplied <= set(context).union(*(set(option) for option in options)) and any(set(option) <= supplied for option in options)


def verdict_correct(claim, expected):
    return claim['verdict'] in expected.get('accepted_verdicts', [expected['verdict']])


def grade(directory, trusted):
    trusted = Path(trusted)
    gold = parse((trusted / 'gold.json').read_bytes())
    checks = dict.fromkeys(('financial_answer', 'numerical_tables', 'claim_verdicts',
                           'evidence', 'robustness', 'delivery'))
    details, errors = {'tables': {}, 'claims': {}}, []
    def result():
        verified = all(checks[key] is True for key in ('financial_answer', 'evidence', 'robustness'))
        strict = verified and checks['delivery'] is True
        return {'scorer_version': SCORER_VERSION, 'complete': strict,
                'verified_research_completion': verified, 'strict_delivery_completion': strict,
                'checks': checks, 'details': details, 'errors': errors}
    if any(digest(trusted / name) != expected for name, expected in gold['hashes'].items()):
        errors.append('trusted_input_changed')
        return result()
    try:
        answer, sql = load_artifacts(directory, gold, parse((trusted / 'schema.json').read_bytes()))
        checks['delivery'] = True
    except Exception as error:
        checks['delivery'] = False
        errors.append('delivery:' + type(error).__name__)
        # Unique, well-formed claims can be diagnosed without running rejected SQL.
        try:
            partial = parse(read_file(Path(directory) / 'answer.json', 65536))
            claims = partial.get('claims', [])
            if partial.get('task_id') == gold['task_id'] and isinstance(claims, list) and len(claims) <= 4:
                schema = parse((trusted / 'schema.json').read_bytes())
                validator = Draft202012Validator(schema['properties']['claims']['items'])
                for claim in claims:
                    if (isinstance(claim, dict) and claim.get('id') in gold['claims']
                            and sum(isinstance(item, dict) and item.get('id') == claim['id'] for item in claims) == 1
                            and validator.is_valid(claim)):
                        expected = gold['claims'][claim['id']]
                        details['claims'][claim['id']] = {
                            'verdict': verdict_correct(claim, expected),
                            'evidence': supported(claim['evidence'], expected['evidence'], expected.get('context_evidence_allowed', [])),
                            'partial_only': True}
        except Exception:
            pass
        return result()
    numbers, claims, evidence, preservation = [], [], [], []
    for table in answer['tables']:
        identifier, spec = table['id'], gold['tables'][table['id']]
        original_error = comparison_error(replay(sql[identifier], trusted / 'data.sqlite'), spec, spec['rows'])
        item = {'original': original_error is None, 'original_error': original_error,
                'evidence': supported(table['evidence'], spec['evidence'], spec.get('context_evidence_allowed', [])),
                'controls': {}, 'control_errors': {}}
        for control in gold['controls']:
            error = comparison_error(replay(sql[identifier], trusted / control['database']), spec,
                                     control['tables'][identifier])
            item['controls'][control['name']] = error is None
            item['control_errors'][control['name']] = error
        details['tables'][identifier] = item
        numbers.append(item['original'])
        preservation.append(all(item['controls'].values()))
        evidence.append(item['evidence'])
        errors.extend(identifier + ':' + name for name in ('original', 'evidence') if not item[name])
        errors.extend(identifier + ':control:' + name for name, passed in item['controls'].items() if not passed)
    for claim in answer['claims']:
        identifier, expected = claim['id'], gold['claims'][claim['id']]
        item = {'verdict': verdict_correct(claim, expected),
                'evidence': supported(claim['evidence'], expected['evidence'], expected.get('context_evidence_allowed', []))}
        details['claims'][identifier] = item
        claims.append(item['verdict'])
        evidence.append(item['evidence'])
        errors.extend(identifier + ':' + name for name, passed in item.items() if not passed)
    checks['numerical_tables'], checks['claim_verdicts'] = all(numbers), all(claims)
    checks['financial_answer'] = checks['numerical_tables'] and checks['claim_verdicts']
    checks['evidence'], checks['robustness'] = all(evidence), all(preservation)
    return result()
