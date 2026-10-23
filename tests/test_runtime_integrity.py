"""Focused unit checks for native context identity and diagnostic retention."""
import json
from pathlib import Path
import sqlite3
import os
import types

import pytest

pytest.importorskip("harbor")
from workpaperbench.runtime_integrity import (
    RuntimeInputIntegrityError, VerifiedDockerEnvironment, file_inventory, stage_context)


def context(root, value):
    root.mkdir()
    (root / "Dockerfile").write_text("FROM scratch\nRUN true\nCOPY data.sqlite /workspace/\n")
    with sqlite3.connect(root / "data.sqlite") as db:
        db.execute("CREATE TABLE sample(value INTEGER)")
        db.execute("INSERT INTO sample VALUES (?)", (value,))
    os.utime(root / "data.sqlite", ns=(1000000000, 1000000000))
    return root


def test_content_identity_separates_equal_metadata_without_changing_dependencies(tmp_path):
    first, second = context(tmp_path / "first", 101), context(tmp_path / "second", 909)
    assert (first / "data.sqlite").stat().st_size == (second / "data.sqlite").stat().st_size
    assert (first / "data.sqlite").stat().st_mtime_ns == (second / "data.sqlite").stat().st_mtime_ns
    before = file_inventory(first), file_inventory(second)
    a, a_hash, _ = stage_context(first)
    b, b_hash, _ = stage_context(second)
    try:
        assert a_hash != b_hash
        for source, stage, identity in ((first, a, a_hash), (second, b, b_hash)):
            dockerfile = (Path(stage.name) / "Dockerfile").read_text().splitlines()
            assert dockerfile[:2] == ["FROM scratch", "RUN true"]
            sources, target = json.loads(dockerfile[2][5:])
            assert target == "/workspace/"
            assert (Path(stage.name) / sources).read_bytes() == (source / "data.sqlite").read_bytes()
            assert identity in sources
        assert before == (file_inventory(first), file_inventory(second))
    finally:
        a.cleanup()
        b.cleanup()


@pytest.mark.parametrize("name,contents", [
    (".dockerignore", "secret\n"),
    ("docker-compose.yaml", "services:\n  main:\n    volumes: [./private:/workspace]\n"),
    ("Dockerfile", "FROM scratch\nCOPY --from=other /x /y\n"),
])
def test_unsupported_context_semantics_fail_closed(tmp_path, name, contents):
    root = context(tmp_path / "input", 1)
    (root / name).write_text(contents)
    with pytest.raises(ValueError):
        stage_context(root)


def test_pristine_verifier_compose_is_preserved(tmp_path):
    root = context(tmp_path / "input", 1)
    (root / "docker-compose.yaml").write_text("services:\n  main:\n    network_mode: none\n")
    stage, _, _ = stage_context(root)
    try:
        assert (Path(stage.name) / "docker-compose.yaml").read_bytes() == (root / "docker-compose.yaml").read_bytes()
    finally:
        stage.cleanup()


def test_input_failure_survives_missing_container_identity(tmp_path, monkeypatch):
    environment = object.__new__(VerifiedDockerEnvironment)
    environment.role = "verifier"
    environment.binding = {"manifest_id": "external", "task_id": "selected"}
    environment.expected = {"data.sqlite": {"sha256": "expected"}}
    environment.diagnostics = tmp_path
    environment.source_context = Path("/canonical/tests")
    environment.environment_dir = Path("/staged")
    environment.context_identity = "content"
    environment.session_id = "offline"
    monkeypatch.setattr(environment, "_container_identity", lambda: (_ for _ in ()).throw(RuntimeError("offline")))
    with pytest.raises(RuntimeInputIntegrityError, match="verifier:data.sqlite"):
        environment._record_probe({"data.sqlite": {"sha256": "wrong", "size": 1}}, "before-grading")
    receipt = json.loads((tmp_path / "offline-before-grading.json").read_text())
    assert receipt["mismatches"][0]["actual_sha256"] == "wrong"
    assert receipt["container_identity_error"] == "RuntimeError"
    assert receipt["outcome"] == "infrastructure_input_integrity"
    assert (tmp_path / "offline-before-grading.json").stat().st_mode & 0o777 == 0o600


def test_build_copy_log_has_private_permissions(tmp_path, monkeypatch):
    import asyncio
    from harbor.environments.docker.docker import DockerEnvironment
    environment = object.__new__(VerifiedDockerEnvironment)
    environment.diagnostics = tmp_path
    environment.session_id = "offline"
    environment.environment_dir = tmp_path

    async def build(self, command, *args, **kwargs):
        return types.SimpleNamespace(return_code=0, stdout="offline build")

    monkeypatch.setattr(DockerEnvironment, "_run_docker_compose_command", build)
    asyncio.run(environment._run_docker_compose_command(["build"]))
    assert (tmp_path / "offline-build-copy.jsonl").stat().st_mode & 0o777 == 0o600
