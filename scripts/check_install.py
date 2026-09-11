"""Key-free native installation and CLI argument diagnostic on the hosted runner."""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import tempfile


def validate_key_free_environment():
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("RUNNER_OS") != "Linux"
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)):
        raise RuntimeError("Key-free installation smoke requires a Linux GitHub Actions runner")
    if any(name.endswith("API_KEY") or name in ("GH_TOKEN", "GITHUB_TOKEN") for name in os.environ):
        raise RuntimeError("Installation diagnostic must be key-free")


def native_hook_smoke_script():
    return "\n".join((
        "import hermes_bootstrap",
        "import json,os,sys,time,yaml",
        "from pathlib import Path",
        "from hermes_cli.plugins import discover_plugins,get_plugin_manager",
        "from hermes_cli.lifecycle import invoke_hook",
        "hooks=('pre_api_request','post_api_request','api_request_error')",
        "config=yaml.safe_load(Path('/tmp/hermes/config.yaml').read_text())",
        "if config.get('plugins',{}).get('enabled') != ['native-api-observer']:",
        "    raise SystemExit(43)",
        "discover_plugins()",
        "manager=get_plugin_manager()",
        "registered={name:bool(manager.has_hook(name)) for name in hooks}",
        "if not all(registered.values()): raise SystemExit(41)",
        "request_id='wpb-check-install-retry-observer'",
        "started=time.time()",
        "common={'task_id':'key-free-check','turn_id':'key-free-check','api_request_id':request_id,",
        "        'api_call_count':1,'retry_count':0,'max_retries':5,'started_at':started}",
        "invoke_hook('pre_api_request',**common)",
        "invoke_hook('api_request_error',**{**common,'retry_count':1,'ended_at':started+0.1,",
        "             'status_code':503,'retryable':True})",
        "invoke_hook('pre_api_request',**common)",
        "invoke_hook('post_api_request',**{**common,'ended_at':started+0.2})",
        "print('WPB_NATIVE_HOOK_SMOKE:'+json.dumps({",
        "    'registered':registered,'dispatches':4,'runtime_config_observer_enabled':True,",
        "    'installed_runtime_python':sys.executable,",
        "    'resolved_native_launch_python':os.environ.get('WPB_NATIVE_LAUNCH_PYTHON'),",
        "    'installed_runtime_commit':os.environ.get('WPB_INSTALLED_RUNTIME_COMMIT'),",
        "    'native_process_can_write_observer_ledger':os.access('/logs/agent/native-api-observer.jsonl',os.W_OK),",
        "},sort_keys=True))",
    ))


def native_failure_diagnostics(text):
    """Return a short error-only summary without retaining prompts or credentials."""
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", str(text or ""))
    text = re.sub(r"(?i)Bearer\s+\S+", "Bearer [redacted]", text)
    text = re.sub(
        r"(?i)(sk-or-v1-[A-Za-z0-9_-]{16,}|sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{16,})",
        "[redacted]", text)
    text = re.sub(r"(?i)(OPENROUTER_API_KEY|[A-Z0-9_]*API_KEY)(\s*[=:]\s*)\S+", r"\1\2[redacted]", text)
    relevant = re.compile(
        r"(?i)(traceback|\b(error|exception|failed|failure)\b|not found|no such file|"
        r"permission denied|module|plugin|config\.yaml|exit status|command failed|"
        r"not executable|not a directory|systemexit)"
    )
    lines = []
    for line in text.splitlines():
        if relevant.search(line):
            line = re.sub(r"\s+", " ", line).strip()[:240]
            if line and line not in lines:
                lines.append(line)
        if len(lines) >= 12:
            break
    return lines


def native_hook_smoke_wrapper_writer():
    return "\n".join((
        "import json, pathlib, shlex, sys",
        "target, runtime_json, runtime_commit, checkout = sys.argv[1:]",
        "runtime_command = json.loads(runtime_json)",
        "if not isinstance(runtime_command,list) or not runtime_command or not all(isinstance(v,str) for v in runtime_command): raise SystemExit(42)",
        "runtime_python = runtime_command[0]",
        "wrapper = '\\n'.join((",
        "    '#!/bin/sh',",
        "    'if [ \"$1\" = \"--yolo\" ] && [ \"$2\" = \"chat\" ]; then',",
        "    '  test \"$(git -C ' + shlex.quote(checkout) + ' rev-parse HEAD)\" = ' + shlex.quote(runtime_commit),",
        "    '  cd ' + shlex.quote(checkout),",
        "    '  WPB_NATIVE_LAUNCH_PYTHON=' + shlex.quote(runtime_python) + ' WPB_INSTALLED_RUNTIME_COMMIT=' + shlex.quote(runtime_commit) + ' exec ' + shlex.join(runtime_command) + ' 2>&1',",
        "    'fi',",
        "    'exit 0',",
        "    '',",
        "))",
        "path = pathlib.Path(target)",
        "path.parent.mkdir(parents=True, exist_ok=True)",
        "path.write_text(wrapper)",
        "path.chmod(0o755)",
    ))


def native_hook_smoke_command(checkout, expected_commit):
    checkout = str(checkout)
    payload = base64.b64encode(native_hook_smoke_script().encode()).decode()
    resolver = shlex.quote(
        "import base64,json,sys\n"
        "from pathlib import Path\n"
        "root=Path(sys.argv[1]).resolve()\n"
        "sys.path.insert(0,str(root))\n"
        "from hermes_cli._launchers import runtime_command,resolve_store_python\n"
        "native_python=resolve_store_python(root)\n"
        "if native_python is None or not native_python.is_file(): raise SystemExit(42)\n"
        "code=base64.b64decode(sys.argv[2]).decode()\n"
        "print(json.dumps(runtime_command(root,code=code,python=native_python,home='/tmp/hermes')))\n"
    )
    writer = native_hook_smoke_wrapper_writer()
    return ("set -eu\n"
            "export PATH=\"$HOME/.local/bin:$PATH\"\n"
            f"installed_runtime_commit=\"$(git -C {shlex.quote(checkout)} rev-parse HEAD)\"\n"
            f"test \"$installed_runtime_commit\" = {shlex.quote(expected_commit)}\n"
            f"installed_runtime_command=\"$(HERMES_HOME=/tmp/hermes python3 -c {resolver} {shlex.quote(checkout)} {shlex.quote(payload)})\"\n"
            "launcher=\"$HOME/.local/bin/hermes\"\n"
            "if [ -L \"$launcher\" ]; then\n"
            "  rm -- \"$launcher\"\n"
            "  launcher_disposition=symlink_unlinked\n"
            "elif [ -f \"$launcher\" ]; then\n"
            "  if [ -e \"$launcher.key-free-smoke-original\" ] || [ -L \"$launcher.key-free-smoke-original\" ]; then exit 44; fi\n"
            "  mv -- \"$launcher\" \"$launcher.key-free-smoke-original\"\n"
            "  launcher_disposition=file_renamed\n"
            "else\n"
            "  exit 45\n"
            "fi\n"
            f"python3 -c {shlex.quote(writer)} \"$launcher\" \"$installed_runtime_command\" \"$installed_runtime_commit\" {shlex.quote(checkout)}\n"
            "printf '%s\\n' \"WPB_NATIVE_HOOK_SMOKE_WRAPPER:installed:$launcher_disposition\"\n")


async def run_native_hook_smoke(agent_environment, checkout, expected_commit):
    result = await agent_environment.exec(
        command=native_hook_smoke_command(checkout, expected_commit),
        env={"HERMES_HOME": "/tmp/hermes", "OPENROUTER_API_KEY": ""},
        timeout_sec=60)
    prefix = "WPB_NATIVE_HOOK_SMOKE_WRAPPER:installed:"
    states = [line[len(prefix):] for line in (result.stdout or "").splitlines()
              if line.startswith(prefix)]
    disposition = states[0] if len(states) == 1 else None
    return {"wrapper_installed": result.return_code == 0 and disposition in {
                "symlink_unlinked", "file_renamed"},
            "original_launcher_disposition": disposition,
            "return_code": result.return_code}


async def verify_native_hook_smoke(agent_environment, root, expected_commit, setup):
    from native_run import retry_observer_evidence

    # This file is read after Harbor's native Hermes.run has written config.yaml
    # and invoked the replaced final chat command.
    log_result = await agent_environment.exec(
        command="cat /logs/agent/hermes.txt",
        env={"HERMES_HOME": "/tmp/hermes", "OPENROUTER_API_KEY": ""},
        timeout_sec=30)
    prefix = "WPB_NATIVE_HOOK_SMOKE:"
    lines = [line[len(prefix):] for line in (log_result.stdout or "").splitlines()
             if line.startswith(prefix)]
    native_log_text = log_result.stdout or ""
    try:
        runtime_check = json.loads(lines[-1]) if len(lines) == 1 else {}
    except json.JSONDecodeError:
        runtime_check = {}
    ledger_path = (Path(root) / ".raw/install/native-install/agent"
                   / "native-api-observer.jsonl")
    evidence = retry_observer_evidence(ledger_path)
    expected_request_id = hashlib.sha256(b"wpb-check-install-retry-observer").hexdigest()
    starts = [event for event in evidence["events"]
              if event["event"] == "pre_api_request" and event["request_id"] == expected_request_id]
    errors = [event for event in evidence["events"]
              if event["event"] == "api_request_error" and event["request_id"] == expected_request_id]
    posts = [event for event in evidence["events"]
             if event["event"] == "post_api_request" and event["request_id"] == expected_request_id]
    registration_events = [event for event in evidence["events"]
                           if event["event"] == "observer_registered"]
    raw_request_id_absent = False
    if evidence["capture_status"] == "captured" and ledger_path.is_file() and not ledger_path.is_symlink():
        raw_request_id_absent = b"wpb-check-install-retry-observer" not in ledger_path.read_bytes()
    registered = runtime_check.get("registered")
    runtime_dispatches = runtime_check.get("dispatches")
    native_process_can_write = runtime_check.get("native_process_can_write_observer_ledger")
    installed_runtime_python = runtime_check.get("installed_runtime_python")
    installed_runtime_commit = runtime_check.get("installed_runtime_commit")
    expected_hooks = {"pre_api_request", "post_api_request", "api_request_error"}
    runtime_marker_valid = (
        set(runtime_check) == {"registered", "dispatches", "installed_runtime_python",
                               "resolved_native_launch_python",
                               "installed_runtime_commit", "native_process_can_write_observer_ledger",
                               "runtime_config_observer_enabled"}
        and type(runtime_dispatches) is int and runtime_dispatches == 4
        and isinstance(installed_runtime_python, str) and installed_runtime_python.startswith("/")
        and isinstance(runtime_check.get("resolved_native_launch_python"), str)
        and runtime_check["resolved_native_launch_python"].startswith("/")
        and installed_runtime_commit == expected_commit
        and runtime_check.get("runtime_config_observer_enabled") is True
        and type(native_process_can_write) is bool
        and isinstance(registered, dict) and set(registered) == expected_hooks
        and all(type(value) is bool and value is True for value in registered.values())
    )
    evidence_shape_valid = (
        isinstance(evidence, dict)
        and type(evidence.get("event_count")) is int
        and type(evidence.get("capture_truncated_possible")) is bool
        and type(evidence.get("observer_registered")) is bool
        and isinstance(evidence.get("events"), list)
        and all(isinstance(event, dict) and isinstance(event.get("event"), str)
                and type(event.get("observed_at")) in (int, float)
                for event in evidence["events"])
    )
    passed = (
        setup.get("wrapper_installed") is True
        and log_result.return_code == 0
        and runtime_marker_valid
        and native_process_can_write is True
        and evidence_shape_valid
        and evidence["capture_status"] == "captured"
        and evidence["capture_truncated_possible"] is False
        and evidence["event_count"] == 5
        and evidence["observer_registered"] is True
        and len(registration_events) == 1
        and len(starts) == 2
        and [event["attempt_ordinal"] for event in starts] == [1, 2]
        and [event["retry_count"] for event in starts] == [0, 0]
        and len(errors) == 1
        and errors[0]["http_status"] == 503
        and errors[0]["retryable"] is True
        and len(posts) == 1
        and raw_request_id_absent
    )
    return {
        "passed": passed,
        "return_code": setup.get("return_code"),
        "native_config_write_exercised": passed,
        "synthetic_hook_dispatch_replaced_final_chat_command": setup.get("wrapper_installed") is True,
        "provider_calls_made": False,
        "hook_dispatch_followed_native_config_write": (
            runtime_marker_valid and runtime_check.get("runtime_config_observer_enabled") is True
        ),
        "runtime_hooks_registered": registered if isinstance(registered, dict) else {},
        "runtime_marker_valid": runtime_marker_valid,
        "installed_runtime_python_resolved": (
            isinstance(installed_runtime_python, str) and installed_runtime_python.startswith("/")
        ),
        "installed_runtime_python": installed_runtime_python,
        "resolved_native_launch_python": runtime_check.get("resolved_native_launch_python"),
        "installed_runtime_commit": installed_runtime_commit,
        "native_process_can_write_observer_ledger": native_process_can_write is True,
        "ledger_retained_and_readable": evidence_shape_valid and evidence["capture_status"] == "captured",
        "raw_request_id_absent": raw_request_id_absent,
        "event_count": evidence["event_count"],
        "repeated_request_ordinals": [event["attempt_ordinal"] for event in starts],
        "retry_count_reset_observed": len(starts) == 2 and [event["retry_count"] for event in starts] == [0, 0],
        "capture_completeness": evidence["capture_completeness"],
        "capture_limitations": evidence["capture_limitations"],
        "native_log_return_code": log_result.return_code,
        "native_log_error_summary": native_failure_diagnostics(native_log_text),
        "candidate_terminal_access_assumption": (
            "same-container terminal permissions may allow writing the shared /logs/agent mount - not probed"
        ),
    }


async def check():
    from harbor.models.trial.config import TrialConfig
    from harbor.trial.hooks import TrialEvent
    from harbor.trial.trial import Trial

    validate_key_free_environment()
    root = Path(__file__).resolve().parent.parent
    runtime = json.loads((root / "config/runtime.json").read_text())
    install_scratch = root / ".raw/install"
    install_scratch.mkdir(parents=True, exist_ok=True)
    task_root = Path(tempfile.mkdtemp(prefix="native-install-task-", dir=install_scratch))
    shutil.copytree(root / "tasks/wp01", task_root, dirs_exist_ok=True)
    task_toml = task_root / "task.toml"
    task_source = task_toml.read_text()
    allowlist = 'network_mode = "allowlist"\nallowed_hosts = ["openrouter.ai"]'
    if task_source.count(allowlist) != 1:
        raise RuntimeError("key_free_task_network_policy_unexpected")
    task_toml.write_text(task_source.replace(allowlist, 'network_mode = "no-network"'))
    config = TrialConfig.model_validate({
        "task": {"path": str(task_root)}, "trial_name": "native-install",
        "trials_dir": str(root / ".raw/install"), "verifier": {"disable": True},
        "agent": {"name": "hermes", "model_name": runtime["model"]["harbor_model"],
                  "env": {"HERMES_HOME": "/tmp/hermes",
                          "WPB_NATIVE_RETRY_LEDGER": "/logs/agent/native-api-observer.jsonl"},
                  "kwargs": {"version": runtime["hermes"]["release_tag"]},
                  "override_setup_timeout_sec": 1200},
    })
    trial = await Trial.create(config)
    captured = []

    async def setup_output(entry):
        if entry.phase == "agent_setup":
            captured.append(entry.text)
            while sum(len(chunk) for chunk in captured) > 100_000 and len(captured) > 1:
                captured.pop(0)

    trial.add_log_callback(setup_output)
    startup = {}

    async def arguments(event):
        from native_trial import stage_retry_observer

        result = await trial.agent_environment.exec(
            command='export PATH="$HOME/.local/bin:$PATH" && hermes --yolo chat --help',
            env={"HERMES_HOME": "/tmp/hermes"}, timeout_sec=30)
        text = (result.stdout or "") + (result.stderr or "")
        startup.update(return_code=result.return_code,
                       supported_flags={flag: flag in text for flag in ("--model", "--toolsets", "-Q", "--query")})
        if result.return_code:
            startup["key_free_cli_error"] = text[-4000:]
        observer = await stage_retry_observer(
            trial.agent_environment, root, "/tmp/hermes", enable=True,
            ledger_path="/logs/agent/native-api-observer.jsonl")
        startup["retry_observer_registration_smoke"] = observer
        smoke = await run_native_hook_smoke(
            trial.agent_environment, runtime["hermes"]["installed_checkout_path"],
            runtime["hermes"]["resolved_release_commit"])
        startup["native_hook_smoke_setup"] = smoke
        if (result.return_code or not all(startup["supported_flags"].values())
                or observer.get("registration_smoke") is not True
                or observer.get("enabled") is not True
                or smoke.get("wrapper_installed") is not True):
            raise RuntimeError("key_free_native_runtime_setup_failed")
    async def verify_after_agent(event):
        setup = startup.get("native_hook_smoke_setup", {})
        if setup.get("wrapper_installed") is True:
            startup["native_hook_smoke"] = await verify_native_hook_smoke(
                trial.agent_environment, root, runtime["hermes"]["resolved_release_commit"], setup)

    trial.add_hook(TrialEvent.AGENT_START, arguments)
    trial.add_hook(TrialEvent.AGENT_END, verify_after_agent)
    from unittest.mock import patch

    # The synthetic token is only used to let the adapter build its run command.
    # The replacement Hermes launcher dispatches local hooks and never contacts a provider.
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "key-free-diagnostic-placeholder"}):
        result = await trial.run()
    exception = result.exception_info
    observer = startup.get("retry_observer_registration_smoke", {})
    passed = (startup.get("return_code") == 0 and all(startup.get("supported_flags", {}).values())
              and observer.get("registration_smoke") is True
              and observer.get("enabled") is True
              and startup.get("native_hook_smoke", {}).get("passed") is True
              and exception is None)
    diagnostic = {"install_complete": bool(startup), "cli_arguments_valid": passed,
                  "startup": startup, "key_free": True,
                  "exception_type": exception.exception_type if exception else None}
    if exception:
        diagnostic["native_trial_error_summary"] = native_failure_diagnostics(
            getattr(exception, "exception_message", ""))
    if exception and not startup:
        detail = exception.exception_message[-4000:]
        if re.search(r"sk-or-v1-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|PRIVATE KEY", detail):
            detail = "credential_pattern_removed"
        diagnostic["controlled_install_error"] = detail
        output = "".join(captured)
        lines = output.splitlines()
        important = [line for line in lines if re.search(r"error|failed|fatal|exception|traceback|not found|not installed|cannot|denied", line, re.I)]
        excerpt = "\n".join(important)[-8000:]
        if re.search(r"sk-or-v1-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|PRIVATE KEY", excerpt):
            excerpt = "credential_pattern_removed"
        diagnostic["controlled_setup_errors"] = excerpt
    destination = root / "installation-results"
    destination.mkdir(exist_ok=True)
    (destination / "install.json").write_text(json.dumps(diagnostic, indent=2) + "\n")
    shutil.rmtree(task_root, ignore_errors=True)
    print("Native installation and hook dispatch", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(check()))
