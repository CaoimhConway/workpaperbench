import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError
import pytest

from workpaperbench.catalog import load

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('name', ['a.sql', 'reserve_bridge.sql', 'a' * 41 + '.sql'])
def test_public_schema_accepts_permitted_basenames(name):
    _, _, task = load(ROOT, 'workflow-v3', 'b01')
    answer = json.loads((task / 'tests/reference.json').read_text())
    answer['tables'][0]['file'] = name
    Draft202012Validator(json.loads((task / 'environment/schema.json').read_text())).validate(answer)


@pytest.mark.parametrize('name', ['/workspace/a.sql', './a.sql', '../a.sql', 'A.sql',
                                 'a b.sql', 'a.sql\n', 'a' * 42 + '.sql'])
def test_public_schema_rejects_paths_and_invalid_basenames(name):
    _, _, task = load(ROOT, 'workflow-v3', 'b01')
    answer = json.loads((task / 'tests/reference.json').read_text())
    answer['tables'][0]['file'] = name
    with pytest.raises(ValidationError, match='does not match'):
        Draft202012Validator(json.loads((task / 'environment/schema.json').read_text())).validate(answer)


def test_revision_changes_only_identity_and_public_filesystem_contract():
    prior = load(ROOT, 'workflow-v2')
    current = load(ROOT, 'workflow-v3')
    assert current['prior_catalog'] == prior['manifest_id']
    assert current['contract_revision']['number'] == 1
    assert current['scorer_sha256'] == prior['scorer_sha256']
    assert len(current['tasks']) == 30
    changed = {'authoring.json', 'instruction.md', 'environment/schema.json',
               'environment/output_contract.json', 'tests/schema.json', 'tests/gold.json'}
    for key in current['tasks']:
        _, old_spec, old = load(ROOT, 'workflow-v2', key)
        _, new_spec, new = load(ROOT, 'workflow-v3', key)
        assert set(p.relative_to(old) for p in old.rglob('*') if p.is_file()) == set(
            p.relative_to(new) for p in new.rglob('*') if p.is_file())
        for path in old.rglob('*'):
            if not path.is_file() or path.relative_to(old).as_posix() in changed:
                continue
            expected = path.read_bytes()
            if path.suffix in ('.json', '.md', '.toml', '.sh'):
                expected = expected.replace(old_spec['task_id'].encode(), new_spec['task_id'].encode())
            assert (new / path.relative_to(old)).read_bytes() == expected
        old_gold = json.loads((old / 'tests/gold.json').read_text())
        new_gold = json.loads((new / 'tests/gold.json').read_text())
        expected = copy.deepcopy(old_gold)
        expected['task_id'] = new_spec['task_id']
        expected['hashes'] = new_gold['hashes']
        assert new_gold == expected
        schema = json.loads((new / 'environment/schema.json').read_text())
        assert schema == json.loads((new / 'tests/schema.json').read_text())
        Draft202012Validator(schema).validate(json.loads((new / 'tests/reference.json').read_text()))
        instruction = (new / 'instruction.md').read_text()
        assert '/workspace/data.sqlite' in instruction
        assert 'all in /logs/artifacts' in instruction
        assert 'Absolute paths and directory prefixes are rejected' in instruction
        assert 'regular files without symlinks' in instruction
        assert 'each requested table and claim ID exactly once' in instruction
