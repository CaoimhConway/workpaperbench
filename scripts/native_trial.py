"""Invoke the native trial with a read-only pre-solve version check."""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sys


OBSERVER_HOOKS = ("pre_api_request", "post_api_request", "api_request_error")


def observer_stage_command(root, hermes_home):
    plugin = Path(root) / "config/native-api-observer"
    files = {
        name: base64.b64encode((plugin / name).read_bytes()).decode("ascii")
        for name in ("plugin.yaml", "__init__.py")
    }
    payload = base64.b64encode(json.dumps(files, sort_keys=True).encode()).decode("ascii")
    script = (
        "import base64,json,pathlib,sys\n"
        "home=pathlib.Path(sys.argv[2])\n"
        "plugins=home/'plugins'\n"
        "destination=plugins/'native-api-observer'\n"
        "if any(path.is_symlink() for path in (home,plugins,destination)): raise SystemExit(2)\n"
        "plugins.mkdir(parents=True,exist_ok=True)\n"
        "destination.mkdir(exist_ok=True)\n"
        "files=json.loads(base64.b64decode(sys.argv[1]))\n"
        "for name,value in files.items():\n"
        " target=destination/name\n"
        " if target.is_symlink(): raise SystemExit(2)\n"
        " target.write_bytes(base64.b64decode(value))\n"
    )
    return "python3 -c " + shlex.quote(script) + " " + shlex.quote(payload) + " " + shlex.quote(str(hermes_home))


async def stage_retry_observer(agent_environment, root, hermes_home, *, enable=False, ledger_path=""):
    """Stage the pinned hook observer and smoke its real Hermes registration path."""
    env = {"HERMES_HOME": str(hermes_home), "WPB_NATIVE_RETRY_LEDGER": "",
           "OPENROUTER_API_KEY": ""}
    stage = await agent_environment.exec(
        command=observer_stage_command(root, hermes_home), env=env, timeout_sec=30)
    if stage.return_code:
        raise RuntimeError("native_retry_observer_stage_failed")

    doctor = await agent_environment.exec(
        command=("export PATH=\"$HOME/.local/bin:$PATH\" && hermes plugins doctor "
                 + shlex.quote(str(Path(hermes_home) / "plugins/native-api-observer")) + " --ci"),
        env=env, timeout_sec=60)
    doctor_output = (doctor.stdout or "") + (doctor.stderr or "")
    hook_count = re.search(r"registrations:\s+\d+\s+tool\(s\),\s+(\d+)\s+hook\(s\)", doctor_output)
    if doctor.return_code or hook_count is None or int(hook_count.group(1)) != len(OBSERVER_HOOKS):
        raise RuntimeError("native_retry_observer_registration_failed")

    if enable:
        enable_env = {"HERMES_HOME": str(hermes_home),
                      "WPB_NATIVE_RETRY_LEDGER": str(ledger_path),
                      "OPENROUTER_API_KEY": ""}
        activated = await agent_environment.exec(
            command='export PATH="$HOME/.local/bin:$PATH" && hermes plugins enable '
                    "native-api-observer --no-allow-tool-override",
            env=enable_env, timeout_sec=60)
        if activated.return_code:
            raise RuntimeError("native_retry_observer_enable_failed")
    return {"staged": True, "registration_smoke": True,
            "registered_hook_count": int(hook_count.group(1)), "enabled": bool(enable)}


async def run(config_path):
    from harbor.models.trial.config import TrialConfig
    from harbor.trial.hooks import TrialEvent
    from harbor.trial.trial import Trial

    root = Path(__file__).resolve().parent.parent
    runtime = json.loads((root / "config/runtime.json").read_text())
    config = TrialConfig.model_validate_json(config_path.read_text())
    trial = await Trial.create(config)

    async def installed_version(event):
        result = await trial.agent_environment.exec(
            command="git -C " + shlex.quote(runtime["hermes"]["installed_checkout_path"]) + " rev-parse HEAD",
            timeout_sec=10,
        )
        revision = (result.stdout or "").strip()
        if result.return_code or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise RuntimeError("installed_revision_unavailable")
        metadata = {"checkout_commit": revision,
                    "expected_commit": runtime["hermes"]["resolved_release_commit"],
                    "checked_before_solving": True}
        metadata["matches_pin"] = revision == metadata["expected_commit"]
        if config.agent.skills:
            skill = root / runtime["agent"]["treatment_skill_dir"] / "SKILL.md"
            expected = hashlib.sha256(skill.read_bytes()).hexdigest()
            staged = str(trial.agent.skills_dir) + "/contract-check/SKILL.md"
            check = await trial.agent_environment.exec(
                command="sha256sum " + shlex.quote(staged), timeout_sec=10)
            actual = (check.stdout or "").split()
            metadata["treatment_instruction_present"] = skill.read_text() in trial.task.instruction
            metadata["treatment_staged_skill_matches"] = check.return_code == 0 and bool(actual) and actual[0] == expected
            metadata["treatment_sha256"] = expected
        observer_ledger = config.agent.env.get("WPB_NATIVE_RETRY_LEDGER")
        if observer_ledger:
            hermes_home = config.agent.env.get("HERMES_HOME", "/tmp/hermes")
            metadata["native_api_retry_observer"] = await stage_retry_observer(
                trial.agent_environment, root, hermes_home, enable=True,
                ledger_path=observer_ledger)
        destination = root / ".raw/versions" / (config.trial_name + ".json")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(metadata, indent=2) + "\n")
        if not metadata["matches_pin"]:
            raise RuntimeError("installed_revision_mismatch")
        if config.agent.skills and not (metadata["treatment_instruction_present"] and metadata["treatment_staged_skill_matches"]):
            raise RuntimeError("native_treatment_not_delivered")

    trial.add_hook(TrialEvent.AGENT_START, installed_version)
    await trial.run()


def validate_live_environment():
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("RUNNER_OS") != "Linux"
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or not os.environ.get("OPENROUTER_API_KEY")):
        raise SystemExit("Native trials require a supplied capped key on the Linux main-branch Actions runner")


if __name__ == "__main__":
    validate_live_environment()
    asyncio.run(run(Path(sys.argv[1])))
