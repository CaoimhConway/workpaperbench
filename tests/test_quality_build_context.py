import importlib.util
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('build_fails', [False, True])
def test_verifier_build_refreshes_archive_metadata_without_changing_inputs(tmp_path, monkeypatch, build_fails):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    spec = importlib.util.spec_from_file_location('quality_context', ROOT / 'scripts/validate_workflow_quality.py')
    quality = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(quality)
    sources = []
    archive_time = 1_600_000_000_000_000_000
    for value in (1, 2):
        source = tmp_path / str(value) / 'tests'
        source.mkdir(parents=True)
        database = source / 'data.sqlite'
        with sqlite3.connect(database) as connection:
            connection.execute('CREATE TABLE observations (amount INTEGER)')
            connection.execute('INSERT INTO observations VALUES (?)', (value,))
        (source / 'Dockerfile').write_text('FROM fixture\nCOPY . /tests/\n')
        for path in source.iterdir():
            os.utime(path, ns=(archive_time, archive_time))
        sources.append(source)
    databases = [source / 'data.sqlite' for source in sources]
    assert databases[0].stat().st_size == databases[1].stat().st_size
    assert databases[0].stat().st_mtime_ns == databases[1].stat().st_mtime_ns
    assert databases[0].read_bytes() != databases[1].read_bytes()
    snapshots = [{path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                  for path in source.iterdir()} for source in sources]
    contexts = []

    def build(command, check):
        assert command[:5] == ['docker', 'build', '-q', '-t', 'wpb-quality-fixture']
        assert check is True
        context = Path(command[5])
        assert context not in sources
        expected = snapshots[len(contexts)]
        assert {path.name: path.read_bytes() for path in context.iterdir()} == {
            name: data for name, (data, _) in expected.items()}
        assert all(path.stat().st_mtime_ns != expected[path.name][1] for path in context.iterdir())
        contexts.append(context)
        if build_fails:
            raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, 'run', build)
    for source in sources:
        monkeypatch.setattr(sys, 'argv', ['verifier-build', str(source), 'wpb-quality-fixture'])
        if build_fails:
            with pytest.raises(subprocess.CalledProcessError):
                exec(quality.VERIFIER_BUILD, {})
        else:
            exec(quality.VERIFIER_BUILD, {})
        assert not contexts[-1].exists()
    assert len(set(contexts)) == 2
    assert snapshots == [{path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                          for path in source.iterdir()} for source in sources]
