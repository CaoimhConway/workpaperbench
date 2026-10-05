"""Key-free native installation diagnostic on the hosted runner."""
import asyncio
import json
import os
from pathlib import Path
import re


async def check():
    from harbor.models.trial.config import TrialConfig
    from harbor.trial.trial import Trial

    if os.environ.get("RUNNER_OS") != "Linux" or os.environ.get("GITHUB_REPOSITORY") != "CaoimhConway/workpaperbench":
        raise RuntimeError("Dedicated hosted runner required")
    if any(name.endswith("API_KEY") or name in ("GH_TOKEN", "GITHUB_TOKEN") for name in os.environ):
        raise RuntimeError("Installation diagnostic must be key-free")
    root = Path(__file__).resolve().parent.parent
    runtime = json.loads((root / "config/runtime.json").read_text())
    config = TrialConfig.model_validate({
        "task": {"path": str(root / "tasks/wp01")}, "trial_name": "native-install",
        "trials_dir": str(root / ".raw/install"), "install_only": True,
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
    result = await trial.run()
    exception = result.exception_info
    diagnostic = {"install_complete": exception is None, "key_free": True,
                  "exception_type": exception.exception_type if exception else None}
    if exception:
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
    print("Native installation", "passed" if exception is None else "failed")
    return 0 if exception is None else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(check()))
