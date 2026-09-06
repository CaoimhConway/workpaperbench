"""Key-free native installation and CLI argument diagnostic on the hosted runner."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import shlex


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
        "import json,os,time",
        "from hermes_cli.plugins import discover_plugins,get_plugin_manager",
        "from hermes_cli.lifecycle import invoke_hook",
        "hooks=('pre_api_request','post_api_request','api_request_error')",
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
        "    'registered':registered,'dispatches':4,",
        "    'launcher_python':os.environ.get('WPB_HERMES_LAUNCHER_PYTHON') == '1',",
        "    'installed_runtime_commit':os.environ.get('WPB_INSTALLED_RUNTIME_COMMIT'),",
        "    'native_process_can_write_observer_ledger':os.access('/logs/agent/native-api-observer.jsonl',os.W_OK),",
        "},sort_keys=True))",
    ))


def native_hook_smoke_command(checkout, expected_commit):
    script = shlex.quote(native_hook_smoke_script())
    checkout = shlex.quote(str(checkout))
    expected_commit = shlex.quote(expected_commit)
    return ("set -eu\n"
            "export PATH=\"$HOME/.local/bin:$PATH\"\n"
            "hermes_bin=\"$(command -v hermes)\"\n"
            "shebang=\"$(head -n 1 \"$hermes_bin\")\"\n"
            "case \"$shebang\" in\n"
            "  '#!/usr/bin/env python'|'#!/usr/bin/env python3'|'#!/usr/bin/env python3.'*)\n"
            "    interpreter=\"${shebang#\\#!/usr/bin/env }\"\n"
            "    hermes_python=\"$(command -v \"$interpreter\")\"\n"
            "    ;;\n"
            "  '#!'*/python|'#!'*/python[0-9]|'#!'*/python[0-9].*) hermes_python=\"${shebang#\\#!}\" ;;\n"
            "  *) exit 42 ;;\n"
            "esac\n"
            "case \"${hermes_python##*/}\" in python|python[0-9]|python[0-9].*) ;; *) exit 42 ;; esac\n"
            "test -x \"$hermes_python\"\n"
            "export WPB_HERMES_LAUNCHER_PYTHON=1\n"
            f"installed_runtime_commit=\"$(git -C {checkout} rev-parse HEAD)\"\n"
            f"test \"$installed_runtime_commit\" = {expected_commit}\n"
            "export WPB_INSTALLED_RUNTIME_COMMIT=\"$installed_runtime_commit\"\n"
            f"cd {checkout}\n"
            f"\"$hermes_python\" -c {script}\n")


async def run_native_hook_smoke(agent_environment, root, checkout, expected_commit):
    from native_run import retry_observer_evidence

    result = await agent_environment.exec(
        command=native_hook_smoke_command(checkout, expected_commit),
        env={"HERMES_HOME": "/tmp/hermes",
             "WPB_NATIVE_RETRY_LEDGER": "/logs/agent/native-api-observer.jsonl",
             "OPENROUTER_API_KEY": ""},
        timeout_sec=60)
    prefix = "WPB_NATIVE_HOOK_SMOKE:"
    lines = [line[len(prefix):] for line in (result.stdout or "").splitlines()
             if line.startswith(prefix)]
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
    launcher_python = runtime_check.get("launcher_python")
    installed_runtime_commit = runtime_check.get("installed_runtime_commit")
    expected_hooks = {"pre_api_request", "post_api_request", "api_request_error"}
    runtime_marker_valid = (
        set(runtime_check) == {"registered", "dispatches", "launcher_python",
                               "installed_runtime_commit", "native_process_can_write_observer_ledger"}
        and type(runtime_dispatches) is int and runtime_dispatches == 4
        and type(launcher_python) is bool and launcher_python is True
        and installed_runtime_commit == expected_commit
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
        result.return_code == 0
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
        "return_code": result.return_code,
        "runtime_hooks_registered": registered if isinstance(registered, dict) else {},
        "runtime_marker_valid": runtime_marker_valid,
        "hermes_launcher_python_shebang": launcher_python is True,
        "installed_runtime_commit": installed_runtime_commit,
        "native_process_can_write_observer_ledger": native_process_can_write is True,
        "ledger_retained_and_readable": evidence_shape_valid and evidence["capture_status"] == "captured",
        "raw_request_id_absent": raw_request_id_absent,
        "event_count": evidence["event_count"],
        "repeated_request_ordinals": [event["attempt_ordinal"] for event in starts],
        "retry_count_reset_observed": len(starts) == 2 and [event["retry_count"] for event in starts] == [0, 0],
        "capture_completeness": evidence["capture_completeness"],
        "capture_limitations": evidence["capture_limitations"],
        "candidate_terminal_access_assumption": (
            "same-container terminal permissions may allow writing the shared /logs/agent mount; not probed"
        ),
    }


async def check():
    from harbor.models.trial.config import TrialConfig
    from harbor.trial.hooks import TrialEvent
    from harbor.trial.trial import Trial

    validate_key_free_environment()
    root = Path(__file__).resolve().parent.parent
    runtime = json.loads((root / "config/runtime.json").read_text())
    config = TrialConfig.model_validate({
        "task": {"path": str(root / "tasks/wp01")}, "trial_name": "native-install",
        "trials_dir": str(root / ".raw/install"), "verifier": {"disable": True},
        "agent": {"name": "hermes", "model_name": runtime["model"]["harbor_model"],
                  "env": {"HERMES_HOME": "/tmp/hermes"},
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
            trial.agent_environment, root, "/tmp/hermes", enable=True)
        startup["retry_observer_registration_smoke"] = observer
        smoke = await run_native_hook_smoke(
            trial.agent_environment, root, runtime["hermes"]["installed_checkout_path"],
            runtime["hermes"]["resolved_release_commit"])
        startup["native_hook_smoke"] = smoke
        raise RuntimeError("key_free_argument_check_complete")

    trial.add_hook(TrialEvent.AGENT_START, arguments)
    result = await trial.run()
    exception = result.exception_info
    observer = startup.get("retry_observer_registration_smoke", {})
    passed = (startup.get("return_code") == 0 and all(startup.get("supported_flags", {}).values())
              and observer.get("registration_smoke") is True
              and observer.get("enabled") is True
              and startup.get("native_hook_smoke", {}).get("passed") is True)
    diagnostic = {"install_complete": bool(startup), "cli_arguments_valid": passed,
                  "startup": startup, "key_free": True,
                  "exception_type": exception.exception_type if exception else None}
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
    print("Native installation and CLI arguments", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(check()))
