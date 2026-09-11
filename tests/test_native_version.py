import hashlib
import importlib.util
from pathlib import Path
import base64
import subprocess
import sys


MODULE_PATH = Path(__file__).parents[1] / "scripts/fix_native_version.py"
SPEC = importlib.util.spec_from_file_location("fix_native_version", MODULE_PATH)
fix_native_version = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fix_native_version)
CHECK_INSTALL_SPEC = importlib.util.spec_from_file_location(
    "check_install", MODULE_PATH.parent / "check_install.py")
check_install = importlib.util.module_from_spec(CHECK_INSTALL_SPEC)
CHECK_INSTALL_SPEC.loader.exec_module(check_install)


def test_challenge_only_observer_config_is_added_after_native_config_generation(monkeypatch):
    source = (
        b"hermes version\n"
        b'            env["OPENROUTER_API_KEY"] = openrouter_key\n'
        b"--source cli 2>/dev/null\n"
        b"        config_yaml = self._build_config_yaml(cli_model)\n"
    )
    monkeypatch.setattr(
        fix_native_version,
        "ORIGINAL_MODULE_SHA256",
        hashlib.sha256(source).hexdigest(),
    )

    corrected = fix_native_version.corrected_hermes_source(source)

    assert b"hermes --version" in corrected
    assert b'if provider == "openrouter":' in corrected
    assert b"--source oneshot 2>/dev/null" in corrected
    assert (
        b'        if self._extra_env.get("WPB_NATIVE_RETRY_LEDGER"):\n'
        b'            config_yaml += "\\nplugins:\\n  enabled:\\n    - native-api-observer\\n"\n'
    ) in corrected
    assert corrected.count(b"native-api-observer") == 1


def test_observer_config_patch_requires_the_pinned_builder_site():
    for source in (b"", b"        config_yaml = self._build_config_yaml(cli_model)\n" * 2):
        try:
            fix_native_version.add_retry_observer_config(source)
        except SystemExit as error:
            assert str(error) == "Pinned native config builder mismatch"
        else:
            raise AssertionError("unexpected native builder shape was accepted")


def test_key_free_smoke_dispatches_only_after_native_config_write():
    script = check_install.native_hook_smoke_script()
    command = check_install.native_hook_smoke_command(
        "/tmp/hermes/hermes-agent", "8b66a51036c1e20920a17cdd049fdf55c968d683")

    assert script.index("config.yaml") < script.index("discover_plugins()")
    assert "plugins',{}).get('enabled') != ['native-api-observer']" in script
    assert "WPB_NATIVE_HOOK_SMOKE:" in script
    assert "--yolo" in command
    assert "project_python(root)" in command
    assert "8b66a51036c1e20920a17cdd049fdf55c968d683" in command
    assert 'launcher="$HOME/.local/bin/hermes"' in command
    assert "launcher_disposition=symlink_unlinked" in command
    assert "launcher_disposition=file_renamed" in command
    assert "WPB_NATIVE_HOOK_SMOKE_WRAPPER:installed:$launcher_disposition" in command
    assert "/tmp/wpb-native-hook-smoke/home" not in command
    assert command.index("installed_runtime_python=") < command.index('if [ -L "$launcher" ]')


def test_smoke_wrapper_is_syntax_checked_and_never_falls_back_to_native_cli(tmp_path):
    commit = "8b66a51036c1e20920a17cdd049fdf55c968d683"
    checkout = "/tmp/hermes/hermes-agent"
    target = tmp_path / "home/.local/bin/hermes"
    payload = base64.b64encode(check_install.native_hook_smoke_script().encode()).decode()
    subprocess.run(
        [sys.executable, "-c", check_install.native_hook_smoke_wrapper_writer(),
         str(target), "/tmp/hermes/hermes-agent/.venv/bin/python", commit, checkout, payload],
        check=True,
    )

    wrapper = target.read_text()
    syntax = subprocess.run(["sh", "-n", str(target)], capture_output=True, text=True)

    assert syntax.returncode == 0, syntax.stderr
    assert 'if [ "$1" = "--yolo" ] && [ "$2" = "chat" ]; then' in wrapper
    assert commit in wrapper
    assert "native-api-observer" in base64.b64decode(payload).decode()
    assert "exec /tmp/hermes/hermes-agent/.venv/bin/python" in wrapper
    assert " 2>&1\nfi\nexit 0" in wrapper
    assert "hermes-real" not in wrapper


def test_native_failure_diagnostics_are_bounded_and_redact_credentials():
    secret = "sk-or-v1-" + "x" * 24
    output = "\n".join(
        ["Traceback (most recent call last):", f"OPENROUTER_API_KEY={secret}",
         "ModuleNotFoundError: No module named 'yaml'"]
        + [f"Error: diagnostic {index}" for index in range(20)]
    )

    summary = check_install.native_failure_diagnostics(output)

    assert len(summary) == 12
    assert any("Traceback" in line for line in summary)
    assert any("ModuleNotFoundError" in line for line in summary)
    assert all(secret not in line for line in summary)
    assert all(len(line) <= 240 for line in summary)
