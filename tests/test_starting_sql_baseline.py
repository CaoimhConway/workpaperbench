"""Starting and submitted tables must be compared on identical scopes."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location('starting_sql_baseline', Path(__file__).resolve().parents[1] / 'scripts/starting_sql_baseline.py')
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)


@pytest.mark.parametrize('before,after,expected', [(False, True, 'Repair'), (True, True, 'Preservation'),
    (True, False, 'Regression'), (False, False, 'Unrepaired')])
def test_transitions(before, after, expected):
    assert baseline.transition(before, after) == expected


def test_original_preservation_can_be_control_regression():
    before = {'original': True, 'controls': {'duplicate': True}}
    after = {'original': True, 'controls': {'duplicate': False}}
    assert baseline.classify(before, after) == ('Preservation', 'Regression')


def test_controls_must_match_and_unscored_is_not_incorrect():
    with pytest.raises(ValueError, match='incomparable_controls'):
        baseline.classify({'original': True, 'controls': {'old': True}},
                          {'original': True, 'controls': {'new': True}})
    with pytest.raises(ValueError, match='unscored_transition'):
        baseline.transition(None, False)
