"""Invoke the native trial with a read-only pre-solve version check."""
import asyncio
import json
import os
from pathlib import Path
import re
import sys


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
            command="git -C /usr/local/lib/hermes-agent rev-parse HEAD",
            timeout_sec=10,
        )
        revision = (result.stdout or "").strip()
        if result.return_code or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise RuntimeError("installed_revision_unavailable")
        metadata = {"checkout_commit": revision,
                    "expected_commit": runtime["hermes"]["resolved_release_commit"],
                    "checked_before_solving": True}
        metadata["matches_pin"] = revision == metadata["expected_commit"]
        destination = root / ".raw/versions" / (config.trial_name + ".json")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(metadata, indent=2) + "\n")
        if not metadata["matches_pin"]:
            raise RuntimeError("installed_revision_mismatch")

    trial.add_hook(TrialEvent.AGENT_START, installed_version)
    await trial.run()


if __name__ == "__main__":
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_OS") != "Linux" or os.environ.get("GITHUB_REPOSITORY") != "CaoimhConway/workpaperbench":
        raise SystemExit("Native trials require the dedicated hosted Actions repository")
    asyncio.run(run(Path(sys.argv[1])))
