"""Bind native Docker materialization to controller-owned catalog identities."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

from harbor.environments.docker.docker import DockerEnvironment
from harbor.models.task.config import NetworkPolicy
from harbor.models.task.task import Task
from harbor.models.task.verifier_mode import resolve_effective_verifier_env_config

from workpaperbench.catalog import load
from scripts.native_run import credential_in


class RuntimeInputIntegrityError(RuntimeError):
    """Immutable task materialization differs from its selected catalog."""


def file_inventory(directory):
    result = {}
    for path in sorted(Path(directory).rglob("*")):
        if path.is_symlink():
            raise ValueError("runtime_context_symlink")
        if path.is_file():
            data = path.read_bytes()
            result[path.relative_to(directory).as_posix()] = {
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data), "mode": path.stat().st_mode,
                "mtime_ns": path.stat().st_mtime_ns,
            }
    return result


def stage_context(source):
    """Content names prevent metadata-only context transfer from aliasing bytes."""
    source = Path(source)
    if (source / ".dockerignore").exists():
        raise ValueError("unsupported_runtime_context_layout")
    import yaml
    for compose in source.glob("*compose*.y*ml"):
        if yaml.safe_load(compose.read_text()) != {"services": {"main": {"network_mode": "none"}}}:
            raise ValueError("unsupported_runtime_compose_paths")
    files = file_inventory(source)
    identity = hashlib.sha256(json.dumps(
        {name: {key: row[key] for key in ("sha256", "size", "mode")}
         for name, row in files.items()}, sort_keys=True).encode()).hexdigest()
    temporary = tempfile.TemporaryDirectory(prefix="wpb-context-")
    target = Path(temporary.name)
    prefix = "content/" + identity
    payload = target / prefix
    shutil.copytree(source, payload, copy_function=shutil.copy2)
    lines = []
    for line in (source / "Dockerfile").read_text().splitlines():
        if line.lstrip().upper().startswith("COPY "):
            value = line.lstrip()[5:].strip()
            parts = json.loads(value) if value.startswith("[") else shlex.split(value)
            if len(parts) < 2 or any(item.startswith("--") for item in parts):
                raise ValueError("unsupported_runtime_copy_instruction")
            sources, destination = parts[:-1], parts[-1]
            if any(Path(item).is_absolute() or ".." in Path(item).parts for item in sources):
                raise ValueError("unsafe_runtime_copy_source")
            line = "COPY " + json.dumps([
                prefix + "/" + ("" if item in (".", "./") else item)
                for item in sources] + [destination])
        lines.append(line)
    (target / "Dockerfile").write_text("\n".join(lines) + "\n")
    for path in source.glob("*compose*.y*ml"):
        shutil.copy2(path, target / path.name)
    return temporary, identity, files


PROBE = """import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1])
out={}
for name in json.loads(sys.argv[2]):
 p=root/name
 if p.is_symlink() or not p.is_file():
  out[name]={'missing_or_symlink':True}
 else:
  digest=hashlib.sha256()
  with p.open('rb') as stream:
   for chunk in iter(lambda:stream.read(65536),b''):digest.update(chunk)
  out[name]={'sha256':digest.hexdigest(),'size':p.stat().st_size}
print(json.dumps(out))
"""


class VerifiedDockerEnvironment(DockerEnvironment):
    """Native Harbor environment with externally bound input checks."""

    def __init__(self, *, canonical_root, expected_manifest, expected_task,
                 environment_dir, environment_name, trial_paths,
                 execution_instruction_sha256=None, **kwargs):
        dataset, separator, _ = expected_manifest.partition("-canonical-")
        if not separator or not expected_task.startswith(dataset + "-"):
            raise ValueError("runtime_binding_identity")
        key = expected_task[len(dataset) + 1:]
        manifest, spec, canonical = load(Path(canonical_root), dataset, key)
        if manifest["manifest_id"] != expected_manifest or spec["task_id"] != expected_task:
            raise ValueError("runtime_binding_mismatch")
        if environment_name != expected_task:
            raise ValueError("runtime_selected_task_mismatch")
        source = Path(environment_dir)
        if source.name not in ("environment", "tests"):
            raise ValueError("runtime_context_role")
        self.role = "candidate" if source.name == "environment" else "verifier"
        self.canonical = canonical
        self.binding = {"manifest_id": expected_manifest, "task_id": expected_task,
                        "task_sha256": spec["task_sha256"],
                        "manifest_sha256": hashlib.sha256(
                            (Path(canonical_root) / "datasets" / dataset / "manifest.json").read_bytes()
                        ).hexdigest()}
        self.binding_arguments = {"canonical_root": str(canonical_root),
            "expected_manifest": expected_manifest, "expected_task": expected_task}
        self.source_context = source
        self.diagnostics = trial_paths.trial_dir / "runtime-integrity"
        self.diagnostics.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.diagnostics.chmod(0o700)
        self.expected = file_inventory(canonical / source.name)
        if self.role == "candidate":
            self.expected = {name: row for name, row in self.expected.items()
                             if name not in ("Dockerfile", "docker-compose.yaml")}
            instruction = source.parent / "instruction.md"
            instruction_bytes = instruction.read_bytes()
            canonical_instruction = (canonical / "instruction.md").read_bytes()
            instruction_sha = hashlib.sha256(instruction_bytes).hexdigest()
            if instruction_bytes != canonical_instruction:
                if (execution_instruction_sha256 != instruction_sha or
                        not instruction_bytes.startswith(canonical_instruction)):
                    raise RuntimeInputIntegrityError("runtime_instruction_changed")
            self.binding["instruction_sha256"] = instruction_sha
            self.binding["canonical_instruction_sha256"] = hashlib.sha256(canonical_instruction).hexdigest()
            canonical_tests = {name: row["sha256"] for name, row in
                               file_inventory(canonical / "tests").items()}
            selected_tests = {name: row["sha256"] for name, row in
                              file_inventory(source.parent / "tests").items()}
            if selected_tests != canonical_tests:
                raise RuntimeInputIntegrityError("runtime_selected_verifier_context_changed")
            selected = Task(source.parent)
            if selected.short_name != expected_task:
                raise RuntimeInputIntegrityError("runtime_task_identity_changed")
        self.staged, self.context_identity, self.context_files = stage_context(source)
        self._started_integrity = False
        self._closed_integrity = False
        super().__init__(environment_dir=Path(self.staged.name),
                         environment_name=environment_name, trial_paths=trial_paths, **kwargs)

    def _write(self, name, value):
        path = self.diagnostics / name
        path.write_text(json.dumps(value, indent=2) + "\n")
        path.chmod(0o600)

    @staticmethod
    def _safe_text(value):
        return "[credential-pattern content withheld]" if credential_in(value.encode(), "") else value

    async def _run_docker_compose_command(self, command, *args, **kwargs):
        result = None
        error = None
        try:
            result = await super()._run_docker_compose_command(command, *args, **kwargs)
            return result
        except Exception as exc:
            error = str(exc)
            raise
        finally:
            if command and command[0] in ("build", "up", "cp"):
                with (self.diagnostics / (self.session_id + "-build-copy.jsonl")).open("a") as log:
                    log.write(json.dumps({"command": command,
                        "context": str(self.environment_dir),
                        "return_code": result.return_code if result else None,
                        "stdout": self._safe_text(result.stdout or "") if result else None,
                        "error": self._safe_text(error) if error else None}) + "\n")
                (self.diagnostics / (self.session_id + "-build-copy.jsonl")).chmod(0o600)

    def _container_identity(self):
        identifiers = subprocess.check_output(["docker", "ps", "-aq", "--filter",
            "label=com.docker.compose.project=" + self.session_id.lower(),
            "--filter", "label=com.docker.compose.service=main"], text=True).split()
        if len(identifiers) != 1:
            raise RuntimeError("runtime_main_container_identity")
        data = json.loads(subprocess.check_output(["docker", "inspect", identifiers[0]], text=True))[0]
        return {"container_id": data["Id"], "image_id": data["Image"],
                "image_reference": data["Config"]["Image"], "mounts": data["Mounts"],
                "network_mode": data["HostConfig"]["NetworkMode"]}

    def _record_probe(self, actual, phase, identity=None):
        root = "/workspace" if self.role == "candidate" else "/tests"
        mismatches = [{"filename": name, "expected_sha256": row["sha256"],
                       "actual_sha256": actual.get(name, {}).get("sha256")}
                      for name, row in self.expected.items()
                      if actual.get(name, {}).get("sha256") != row["sha256"]]
        record = {**self.binding, "role": self.role, "phase": phase,
            "outcome": "infrastructure_input_integrity" if mismatches else "verified",
            "diagnostic_scope": "local_only_unsuitable_for_publication_without_review",
            "source_context": str(self.source_context), "staged_context": str(self.environment_dir),
            "context_identity": self.context_identity, "session_id": self.session_id,
            "expected": self.expected, "actual": actual, "mismatches": mismatches}
        filename = self.session_id + "-" + phase + ".json"
        self._write(filename, record)
        try:
            identity = identity or self._container_identity()
            record.update(identity)
        except Exception as exc:
            record["container_identity_error"] = type(exc).__name__
        for row in mismatches:
            target = self.diagnostics / (self.role + "-" + row["filename"].replace("/", "_"))
            try:
                if actual.get(row["filename"], {}).get("size", 2**31) > 2 * 1024**2:
                    raise ValueError("diagnostic_file_too_large")
                subprocess.run(["docker", "cp", record["container_id"] + ":" +
                    root + "/" + row["filename"], str(target)], check=True,
                    capture_output=True, timeout=30)
                target.chmod(0o600)
                if target.is_symlink() or target.stat().st_size > 2 * 1024**2:
                    raise ValueError("unsafe_diagnostic_file")
                if credential_in(target.read_bytes(), ""):
                    raise ValueError("credential_pattern_in_diagnostic")
                row["retained_file"] = target.name
            except Exception as exc:
                target.unlink(missing_ok=True)
                row["retention_error"] = type(exc).__name__
        self._write(filename, record)
        if mismatches:
            raise RuntimeInputIntegrityError("runtime_input_integrity_failed:" + self.role + ":" +
                                             ",".join(row["filename"] for row in mismatches))
        return record

    async def verify_inputs(self, phase):
        root = "/workspace" if self.role == "candidate" else "/tests"
        command = "python3 -c " + shlex.quote(PROBE) + " " + root + " " + shlex.quote(json.dumps(list(self.expected)))
        response = await super().exec(command, timeout_sec=30)
        if response.return_code:
            raise RuntimeError("runtime_input_probe_failed")
        return self._record_probe(json.loads(response.stdout), phase)

    @contextmanager
    def with_default_user(self, user):
        # Harbor enters this context after setup and immediately before agent.run,
        # including when the baseline and phase network policies are identical.
        if self.role == "candidate" and self._started_integrity:
            identity = self._container_identity()
            response = subprocess.run(["docker", "exec", identity["container_id"],
                "python3", "-c", PROBE, "/workspace", json.dumps(list(self.expected))],
                check=True, capture_output=True, text=True, timeout=30)
            self._record_probe(json.loads(response.stdout), "before-agent", identity)
        with super().with_default_user(user):
            yield

    async def _trusted_preflight(self):
        config = resolve_effective_verifier_env_config(Task(self.source_context.parent).config, None)
        if config is None:
            raise ValueError("runtime_requires_separate_verifier")
        session = "wpb-trusted-" + hashlib.sha256(self.session_id.encode()).hexdigest()[:24]
        trusted = type(self)(**self.binding_arguments, environment_dir=self.source_context.parent / "tests",
            environment_name=self.environment_name, session_id=session, trial_paths=self.trial_paths,
            task_env_config=config, network_policy=NetworkPolicy(network_mode="no-network"),
            mounts=[], logger=self.logger)
        try:
            await trusted.start(force_build=False)
        finally:
            await trusted.stop(delete=True)

    async def start(self, force_build):
        self._write(self.session_id + "-context.json", {**self.binding, "role": self.role,
            "source_context": str(self.source_context), "staged_context": str(self.environment_dir),
            "context_identity": self.context_identity, "files": self.context_files})
        try:
            await super().start(force_build=force_build)
            self._started_integrity = True
            await self.verify_inputs("setup")
            if self.role == "candidate":
                await self._trusted_preflight()
        except Exception:
            await self.stop(delete=True)
            raise

    async def exec(self, command, *args, **kwargs):
        if self.role == "verifier" and "/tests/test.sh" in command:
            await self.verify_inputs("before-grading")
        return await super().exec(command, *args, **kwargs)

    async def stop(self, delete):
        if self._closed_integrity:
            return
        try:
            await super().stop(delete=delete)
        finally:
            self._closed_integrity = True
            self.staged.cleanup()
