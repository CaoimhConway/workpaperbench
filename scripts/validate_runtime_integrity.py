"""Exercise native materialization and preflight rejection without inference."""
import argparse
import asyncio
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
from threading import Thread
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

from harbor.environments.docker.docker import DockerEnvironment
from harbor.models.trial.config import TrialConfig
from harbor.trial.hooks import TrialEvent
from harbor.trial.trial import Trial
from workpaperbench.catalog import content_hash, load, tree_hash
from workpaperbench.runtime_integrity import VerifiedDockerEnvironment, PROBE, file_inventory, stage_context


class FixtureEndpoint(BaseHTTPRequestHandler):
    requests = 0

    def do_POST(self):
        type(self).requests += 1
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        body = {"fixture": True}
        if self.path == "/v1/chat/completions":
            body = {"id": "offline-integrity-fixture", "object": "chat.completion",
                "created": 0, "model": "integrity-fixture", "choices": [{"index": 0,
                    "message": {"role": "assistant", "content": json.dumps({
                        "analysis": "Scripted protocol fixture", "plan": "Finish",
                        "commands": [], "task_complete": True})}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *args):
        pass


async def exercise(root, dataset, key, output, label, endpoint, injection=None,
                   offline_policy=False, materialization_only=False, native_endpoint=False):
    manifest, spec, task = load(root, dataset, key)
    path = task
    if offline_policy:
        path = output / (label + "-task")
        shutil.copytree(task, path)
        config_path = path / "task.toml"
        text = config_path.read_text().replace('network_mode = "public"', 'network_mode = "no-network"')
        text = re.sub(r"(?m)^allowed_hosts = .*$", "allowed_hosts = []", text)
        config_path.write_text(text)
    config = TrialConfig.model_validate({
        "task": {"path": str(path)}, "trial_name": label,
        "trials_dir": str(output / "trials"),
        "agent": {"name": "nop" if materialization_only else "oracle", "override_timeout_sec": 120},
        "verifier": {"disable": materialization_only},
        "environment": {"type": "docker",
            "import_path": "workpaperbench.runtime_integrity:VerifiedDockerEnvironment",
            "kwargs": {"canonical_root": str(root), "expected_manifest": manifest["manifest_id"],
                       "expected_task": spec["task_id"]}}})
    if native_endpoint:
        config.agent = type(config.agent).model_validate({"name": "terminus-2",
            "model_name": "openai/integrity-fixture", "override_timeout_sec": 120,
            "kwargs": {"api_base": endpoint.rsplit("/", 1)[0] + "/v1",
                "max_turns": 1, "parser_name": "json", "use_responses_api": False,
                "model_info": {"max_input_tokens": 65536, "max_output_tokens": 512,
                    "input_cost_per_token": 0, "output_cost_per_token": 0,
                    "litellm_provider": "openai", "mode": "chat"},
                "llm_call_kwargs": {"max_tokens": 512}}})
        os.environ["OPENAI_API_KEY"] = "offline-fixture-not-a-provider-credential"
    before = FixtureEndpoint.requests
    original_verify = VerifiedDockerEnvironment.verify_inputs

    async def substituted(environment, phase):
        role, filename = {
            "trusted-preflight": ("verifier", "data.sqlite"),
            "trusted-grading": ("verifier", "control-1.sqlite"),
        }.get(injection, (None, None))
        target_phase = "before-grading" if injection == "trusted-grading" else "setup"
        if environment.role == role and phase == target_phase:
            await DockerEnvironment.exec(environment,
                "python3 -c " + __import__("shlex").quote(
                    "from pathlib import Path;Path('/tests/" + filename + "').write_bytes(b'offline wrong trusted bytes')"),
                timeout_sec=10)
        return await original_verify(environment, phase)

    VerifiedDockerEnvironment.verify_inputs = substituted
    try:
        trial = await Trial.create(config)
        original_setup = trial.agent.setup
        original_run = trial.agent.run

        async def setup(environment):
            await original_setup(environment)
            if injection == "candidate":
                await DockerEnvironment.exec(environment,
                    "python3 -c " + __import__("shlex").quote(
                        "from pathlib import Path;Path('/workspace/data.sqlite').write_bytes(b'offline wrong candidate bytes')"),
                    timeout_sec=10)

        async def run(**kwargs):
            with urlopen(Request(endpoint, data=b"scripted protocol fixture", method="POST"), timeout=5) as response:
                assert response.status == 200
            await original_run(**kwargs)

        async def sentinel(event):
            result = await trial.agent_environment.exec(
                "test ! -e /workspace/offline_integrity_sentinel && touch /workspace/offline_integrity_sentinel",
                timeout_sec=10)
            if result.return_code:
                raise AssertionError("candidate_sentinel_survived")
        trial.agent.setup = setup
        if not native_endpoint:
            trial.agent.run = run
        trial.add_hook(TrialEvent.AGENT_START, sentinel)
        result = await trial.run()
    finally:
        VerifiedDockerEnvironment.verify_inputs = original_verify
    receipts = [json.loads(p.read_text()) for p in
                sorted((trial.paths.trial_dir / "runtime-integrity").glob("*.json"))]
    checked = [row for row in receipts if "mismatches" in row]
    bad = [row for row in checked if row["mismatches"]]
    count = FixtureEndpoint.requests - before
    verdict_path = trial.paths.verifier_dir / "verdict.json"
    verdict = json.loads(verdict_path.read_text()) if verdict_path.exists() else None
    row = {"case": label, "task": key, "bundle": manifest["manifest_id"],
           "inference": False, "native_agent": "terminus-2" if native_endpoint else "scripted-oracle",
           "scripted_endpoint_requests": count,
           "exception": result.exception_info.model_dump(mode="json") if result.exception_info else None,
           "checks": [{"role": r["role"], "phase": r["phase"], "mismatches": r["mismatches"],
                       "image_id": r.get("image_id"), "container_id": r.get("container_id")}
                      for r in checked], "verdict": verdict}
    if injection:
        expected_file = "control-1.sqlite" if injection == "trusted-grading" else "data.sqlite"
        assert bad and any(m["filename"] == expected_file for r in bad for m in r["mismatches"]), row
        assert count == (1 if injection == "trusted-grading" else 0), row
        assert result.exception_info and result.exception_info.exception_type == "RuntimeInputIntegrityError", row
        for failed in bad:
            for mismatch in failed["mismatches"]:
                assert mismatch.get("retained_file"), mismatch
        if injection == "trusted-grading":
            assert verdict is None, "Semantic verifier must not run after mismatch"
    else:
        assert not bad and not result.exception_info, row
        assert count == 1, row
        assert any(r["phase"] == "before-agent" and r["role"] == "candidate" for r in checked), row
        assert any(r["phase"] == "setup" and r["role"] == "verifier" for r in checked), row
        if not materialization_only:
            assert any(r["phase"] == "before-grading" and r["role"] == "verifier" for r in checked), row
            assert verdict and all(verdict["checks"].values()), row
    (output / (label + ".json")).write_text(json.dumps(row, indent=2) + "\n")
    print(json.dumps({"case": label, "requests": count, "checks": len(checked), "passed": True}), flush=True)
    return row


def synthetic_catalog(root, destination):
    prior = load(root, "workflow-v12")
    manifest = dict(prior)
    manifest["hashes"] = {}
    manifest["tasks"] = {}
    for key, value in (("a06", 101), ("a07", 909)):
        _, spec, source = load(root, "workflow-v12", key)
        target = destination / "datasets/workflow-v12/tasks" / key
        shutil.copytree(source, target)
        database = target / "environment/data.sqlite"
        database.unlink()
        with sqlite3.connect(database) as db:
            db.execute("CREATE TABLE synthetic_measurement(value INTEGER)")
            db.execute("INSERT INTO synthetic_measurement VALUES (?)", (value,))
        for db_path in [database, *(target / "tests").glob("*.sqlite")]:
            if db_path != database:
                shutil.copyfile(database, db_path)
            os.utime(db_path, ns=(1792623888000000000, 1792623888000000000))
        manifest["tasks"][key] = {**spec, "task_sha256": tree_hash(target)}
    a = destination / manifest["tasks"]["a06"]["path"] / "environment/data.sqlite"
    b = destination / manifest["tasks"]["a07"]["path"] / "environment/data.sqlite"
    assert a.stat().st_size == b.stat().st_size and a.stat().st_mtime_ns == b.stat().st_mtime_ns
    assert a.read_bytes() != b.read_bytes()
    manifest["content_hash"] = content_hash(manifest)
    manifest["manifest_id"] = "workflow-v12-canonical-" + manifest["content_hash"][:12]
    (destination / "datasets/workflow-v12/manifest.json").write_text(json.dumps(manifest))
    return manifest["manifest_id"]


def cold_catalog(root, destination):
    """Change only a harmless COPY operand so dependency layers stay reusable."""
    manifest = dict(load(root, "workflow-v12"))
    manifest["hashes"] = {}
    manifest["tasks"] = {}
    import uuid
    for key in ("a06", "a07"):
        _, spec, source = load(root, "workflow-v12", key)
        target = destination / spec["path"]
        shutil.copytree(source, target, copy_function=shutil.copy2)
        nonce = uuid.uuid4().hex
        for role in ("environment", "tests"):
            (target / role / "offline-copy-cache-probe.txt").write_text(nonce + role)
        dockerfile = target / "environment/Dockerfile"
        dockerfile.write_text(dockerfile.read_text().replace(
            "output_contract.json /workspace/", "output_contract.json offline-copy-cache-probe.txt /workspace/"))
        manifest["tasks"][key] = {**spec, "task_sha256": tree_hash(target)}
    manifest["content_hash"] = content_hash(manifest)
    manifest["manifest_id"] = "workflow-v12-canonical-" + manifest["content_hash"][:12]
    (destination / "datasets/workflow-v12/manifest.json").write_text(json.dumps(manifest))
    return manifest["manifest_id"]


def validate_measurements(args, output):
    """Reuse the constrained separate-verifier protocol for authored SQL mutants."""
    import base64
    import subprocess
    from validate_workflow_quality import CONTAINER
    from validate_workflow_contract_revision import execute_container
    from workflow_dependency_cases import frozen_columns
    report = {"inference": False, "dataset": args.dataset, "cases": []}
    for key in ("a03", "a05", "a06"):
        manifest, spec, task = load(ROOT, args.dataset, key)
        stage, identity, expected = stage_context(task / "tests")
        tag = "wpb-measurement-" + spec["task_sha256"][:16]
        try:
            subprocess.run(["docker", "build", "-q", "-t", tag, stage.name],
                           capture_output=True, check=True, timeout=120)
            probe = subprocess.run(["docker", "run", "--rm", "--network", "none",
                "--read-only", "--entrypoint", "python3", tag, "-c", PROBE,
                "/tests", json.dumps(list(expected))], capture_output=True,
                text=True, check=True, timeout=30)
            actual = json.loads(probe.stdout)
            assert all(actual[name]["sha256"] == row["sha256"] for name, row in expected.items())
            gold = json.loads((task / "tests/gold.json").read_text())
            answer = (task / "tests/reference.json").read_text()
            for variant in ("reference", "frozen-derived", "zero-residual"):
                files = {"answer.json": answer.encode()}
                for name, table in gold["tables"].items():
                    sql = (task / "solution" / (name + ".sql")).read_text()
                    if variant == "frozen-derived":
                        sql = frozen_columns(sql, table, [n for n in table["columns"] if n not in table["keys"]])
                    elif variant == "zero-residual":
                        columns = [("0 AS " if "residual" in n else "") + '"' + n + '"'
                                   for n in table["columns"]]
                        sql = "SELECT " + ",".join(columns) + " FROM (" + sql.strip().rstrip(";") + ")"
                    files[name + ".sql"] = sql.encode()
                payload = json.dumps({n: base64.b64encode(raw).decode() for n, raw in files.items()}).encode()
                result = execute_container(tag, CONTAINER, payload)
                result.check_returncode()
                verdict = json.loads(result.stdout)
                assert all(verdict["isolation"].values())
                if variant == "reference":
                    assert verdict["complete"] and all(verdict["checks"].values()), verdict
                else:
                    assert verdict["complete"] is False, verdict
                    assert verdict["checks"]["robustness"] is False, verdict
                    assert any(value is False for table in verdict["details"]["tables"].values()
                               for value in table["controls"].values()), verdict
                report["cases"].append({"task": key, "variant": variant,
                    "manifest_id": manifest["manifest_id"], "task_sha256": spec["task_sha256"],
                    "context_identity": identity, "verifier_assets_verified": True,
                    "files_sha256": {n: hashlib.sha256(raw).hexdigest() for n, raw in files.items()},
                    "verdict": verdict, "passed": True})
                (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
                print(key, variant, "passed", flush=True)
        finally:
            stage.cleanup()
            subprocess.run(["docker", "image", "rm", tag], capture_output=True, check=False)
    return report


async def main(args):
    if sys.platform != "linux":
        raise SystemExit("Run this offline fixture on the dedicated Linux Docker controller")
    for name in list(os.environ):
        if re.search(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", name, re.I):
            del os.environ[name]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    if args.mode == "grading":
        validate_measurements(args, output)
        return
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureEndpoint)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = "http://127.0.0.1:" + str(server.server_port) + "/fixture"
    report = {"inference": False, "source_files_sha256": {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in ("workpaperbench/runtime_integrity.py", "scripts/validate_runtime_integrity.py")},
        "cases": []}

    async def add(*a, **kw):
        report["cases"].append(await exercise(*a, **kw))
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    try:
        if args.mode == "cold":
            with tempfile.TemporaryDirectory(prefix="wpb-targeted-copy-cold-") as temp:
                cold_catalog(ROOT, Path(temp))
                for key in ("a06", "a07"):
                    await add(Path(temp), "workflow-v12", key, output, "copy-cold-" + key, endpoint)
        elif args.mode == "regressions":
            for key in ("a06", "a07", "a06", "a07"):
                await add(ROOT, args.dataset, key, output,
                          "warm-" + str(len(report["cases"])) + "-" + key, endpoint)
            for injection in ("candidate", "trusted-preflight", "trusted-grading"):
                await add(ROOT, args.dataset, "a07", output, injection, endpoint,
                          injection=injection, offline_policy=injection == "candidate")
            for injection in (None, "candidate", "trusted-preflight"):
                await add(ROOT, args.dataset, "a07", output,
                          "native-endpoint-" + (injection or "positive"), endpoint,
                          injection=injection, native_endpoint=True, materialization_only=True)
            with tempfile.TemporaryDirectory(prefix="wpb-equal-metadata-") as temp:
                synthetic_catalog(ROOT, Path(temp))
                for key in ("a06", "a07", "a06", "a07"):
                    await add(Path(temp), "workflow-v12", key, output,
                              "equal-metadata-" + str(len(report["cases"])), endpoint,
                              materialization_only=True)
        else:
            manifest = load(ROOT, args.dataset)
            for key in sorted(manifest["tasks"]):
                spec = manifest["tasks"][key]
                if spec["split"] == "evaluation":
                    await add(ROOT, args.dataset, key, output, "ordered-" + key, endpoint, materialization_only=True)
    finally:
        server.shutdown()
        thread.join()
    print(str(output / "report.json"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="workflow-v12")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("regressions", "ordered", "cold", "grading"), default="regressions")
    asyncio.run(main(parser.parse_args()))
