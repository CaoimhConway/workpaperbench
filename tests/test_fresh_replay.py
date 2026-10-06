"""Focused controls for immutable, inference-free answer replay."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fresh_replay


RUN_ENV = {
    "GITHUB_ACTIONS": "true",
    "RUNNER_OS": "Linux",
    "GITHUB_RUN_ID": "1234",
    "GITHUB_RUN_ATTEMPT": "1",
    "GITHUB_SHA": "a" * 40,
    "GITHUB_REPOSITORY": "example/workpaperbench",
    "PATH": "/usr/bin:/bin",
}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")
    return path.read_bytes()


def task_tree(root, task_key="wp01", task_id="wp01", base="tasks"):
    task = root / base / task_key
    (task / "tests/workpaperbench").mkdir(parents=True)
    (task / "solution").mkdir()
    write_json(task / "tests/gold.json", {"task_id": task_id})
    (task / "tests/workpaperbench/grading.py").write_text("# historical grader\n")
    (task / "tests/workpaperbench/sql_worker.py").write_text("# historical worker\n")
    (task / "solution/solve.sh").write_text("#!/bin/bash\nexit 0\n")
    return task


def install_historical(root, answer=None, verdict=None):
    slot = {"slot_id": "final-wp01-A-1", "task": "wp01", "arm": "A",
            "repetition": 1, "campaign": "final", "split": "evaluation"}
    manifest = {"manifest_id": "historical-test", "hashes": {}}
    write_json(root / "config/freeze.json", manifest)
    write_json(root / "config/schedule.json", [slot])
    task_tree(root)
    directory = root / "reports/runs" / slot["slot_id"]
    directory.mkdir(parents=True)
    answer = answer or json.dumps({"task_id": "wp01", "answers": [], "conclusion": None}).encode()
    answer_path = directory / "answer.raw.txt"
    answer_path.write_bytes(answer)
    record = {**slot, "freeze_manifest_id": manifest["manifest_id"], "run_id": "77",
              "commit_sha": "b" * 40, "github_run_attempt": "1", "raw_sha256": hashlib.sha256(answer).hexdigest()}
    if verdict is not None:
        write_json(directory / "verdict.json", verdict)
    record_bytes = write_json(directory / "record.json", record)
    hashes = {"record.json": hashlib.sha256(record_bytes).hexdigest(),
              "answer.raw.txt": hashlib.sha256(answer).hexdigest()}
    if verdict is not None:
        hashes["verdict.json"] = hashlib.sha256((directory / "verdict.json").read_bytes()).hexdigest()
    write_json(directory / "artifact-audit.json", {
        "archive_digest_verified": True,
        "declared_slots": [slot["slot_id"]],
        "workflow_run": {"id": 77, "head_sha": "b" * 40, "run_attempt": 1},
        "retained_file_sha256": hashes,
    })
    return slot, directory


def set_host_env(monkeypatch):
    for name, value in RUN_ENV.items():
        monkeypatch.setenv(name, value)
    for name in ("OPENROUTER_API_KEY", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def fake_native(monkeypatch):
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        assert kwargs["env"].get("OPENROUTER_API_KEY") is None
        assert kwargs["env"].get("GH_TOKEN") is None
        trial_name = command[command.index("--trial-name") + 1]
        trials = Path(command[command.index("--trials-dir") + 1])
        write_json(trials / trial_name / "verifier/verdict.json", {
            "complete": False,
            "checks": {"format": True, "replay": False},
            "isolation": {"network_namespace_none": True, "network_probe_blocked": True,
                          "no_inference_key": True, "no_docker_socket": True},
        })
        return None

    monkeypatch.setattr(fresh_replay.subprocess, "run", run)
    return calls


def test_historical_replay_uses_retained_hashes_and_ignores_regrade_sidecar(tmp_path, monkeypatch):
    prior = {"complete": False, "checks": {"format": True, "replay": True}}
    _, directory = install_historical(tmp_path, verdict=prior)
    write_json(directory / "regrade.json", {"complete": True, "cached": True})
    set_host_env(monkeypatch)
    calls = fake_native(monkeypatch)

    receipts = fresh_replay.replay_selected(tmp_path, "historical", "all", env=RUN_ENV)

    assert len(calls) == 1
    receipt = json.loads(receipts[0].read_text())
    assert receipt["input_source"] == "retained_artifact"
    assert len(receipt["receipt_identity_sha256"]) == 64
    assert receipt["input_sha256"] == hashlib.sha256((directory / "answer.raw.txt").read_bytes()).hexdigest()
    assert receipt["scorer_sha256"] == hashlib.sha256(
        (ROOT / "workpaperbench/grading.py").read_bytes() + (ROOT / "workpaperbench/sql_worker.py").read_bytes()
    ).hexdigest()
    assert receipt["effective_task_scorer_sha256"] != receipt["scorer_sha256"]
    assert receipt["comparison"] == {"prior_available": True, "complete_same": True, "checks_same": False}
    assert (directory / "verdict.json").read_text() == json.dumps(prior, sort_keys=True) + "\n"
    assert (tmp_path / "tasks/wp01/tests/workpaperbench/grading.py").read_text() == "# historical grader\n"


def test_replay_receipt_is_create_only(tmp_path):
    value = {"complete": True}
    fresh_replay.write_receipt(tmp_path, "1234", "1", "historical", "final-wp01-A-1", value)
    with pytest.raises(FileExistsError):
        fresh_replay.write_receipt(tmp_path, "1234", "1", "historical", "final-wp01-A-1", {"complete": False})


def test_only_hosted_linux_without_secrets_is_accepted():
    assert fresh_replay.require_hosted_linux(RUN_ENV) == ("1234", "1", "a" * 40)
    with pytest.raises(ValueError, match="hosted_linux"):
        fresh_replay.require_hosted_linux({**RUN_ENV, "RUNNER_OS": "macOS"})
    with pytest.raises(ValueError, match="secret_environment"):
        fresh_replay.require_hosted_linux({**RUN_ENV, "OPENROUTER_API_KEY": "synthetic"})


def test_answer_path_is_bounded_scoped_and_identity_checked(tmp_path):
    task_tree(tmp_path)
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    answer = submissions / "answer.json"
    write_json(answer, {"task_id": "wp01", "answers": [], "conclusion": None})

    content, task_dir, slot, input_name, prior = fresh_replay.user_answer(
        tmp_path, "submissions/answer.json", "wp01", "historical"
    )
    assert task_dir == (tmp_path / "tasks/wp01").resolve()
    assert slot["slot_id"] == "answer-wp01"
    assert input_name == "submissions/answer.json"
    assert prior is None
    with pytest.raises(ValueError, match="task_identity_mismatch"):
        fresh_replay.check_answer_identity(b'{"task_id":"wp02"}', "wp01")
    with pytest.raises(ValueError, match="submissions"):
        fresh_replay.user_answer(tmp_path, "tasks/wp01/instruction.md", "wp01", "historical")
    with pytest.raises(ValueError, match="must_be_json"):
        write_json(tmp_path / "submissions/answer.txt", {"task_id": "wp01"})
        fresh_replay.user_answer(tmp_path, "submissions/answer.txt", "wp01", "historical")


def test_real_v1_user_answer_requires_manifest_task_identity(tmp_path):
    task = task_tree(tmp_path, task_id="real-v1-wp01", base="datasets/real-v1/tasks")
    write_json(tmp_path / "submissions/real.json", {"task_id": "real-v1-wp01"})
    tasks = {"wp01": {"task_id": "real-v1-wp01", "path": "datasets/real-v1/tasks/wp01"}}

    content, resolved_task, _, _, _ = fresh_replay.user_answer(
        tmp_path, "submissions/real.json", "wp01", "real-v1", tasks
    )
    assert json.loads(content)["task_id"] == "real-v1-wp01"
    assert resolved_task == task.resolve()
    with pytest.raises(ValueError, match="task_identity_mismatch"):
        write_json(tmp_path / "submissions/wrong.json", {"task_id": "wp01"})
        fresh_replay.user_answer(tmp_path, "submissions/wrong.json", "wp01", "real-v1", tasks)


def test_user_answer_rejects_oversize_and_symlink(tmp_path):
    task_tree(tmp_path)
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    (submissions / "large.json").write_bytes(b" " * (fresh_replay.MAX_ANSWER + 1))
    with pytest.raises(ValueError, match="file_too_large"):
        fresh_replay.user_answer(tmp_path, "submissions/large.json", "wp01", "historical")
    (submissions / "answer.json").write_text('{"task_id":"wp01"}')
    (submissions / "link.json").symlink_to(submissions / "answer.json")
    with pytest.raises(ValueError, match="symlink_path_rejected"):
        fresh_replay.user_answer(tmp_path, "submissions/link.json", "wp01", "historical")


def test_task_tree_hash_rejects_symlinks(tmp_path):
    task = task_tree(tmp_path)
    (task / "tests/link").symlink_to(task / "tests/gold.json")
    with pytest.raises(ValueError, match="symlink"):
        fresh_replay.tree_sha256(task)
