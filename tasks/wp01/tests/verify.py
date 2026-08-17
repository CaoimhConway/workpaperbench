"""Trusted separate-verifier entry point."""
import json
import os
from pathlib import Path
import sys
import socket
import ssl

sys.path.insert(0, "/tests")
from workpaperbench.grading import grade

output = Path("/logs/verifier")
output.mkdir(exist_ok=True, parents=True)
network_blocked = False
try:
    with socket.create_connection(("1.1.1.1", 443), timeout=2) as transport:
        with ssl.create_default_context().wrap_socket(transport, server_hostname="one.one.one.one"):
            pass
except Exception:
    network_blocked = True
if any(k in os.environ for k in ("OPENROUTER_API_KEY", "GITHUB_TOKEN", "GH_TOKEN")):
    verdict = {"complete": False, "checks": {}, "errors": ["verifier_has_secret"]}
elif not network_blocked or Path("/var/run/docker.sock").exists():
    verdict = {"complete": False, "checks": {}, "errors": ["verifier_boundary"]}
else:
    verdict = grade("/logs/artifacts", "/tests")
verdict["isolation"] = {"network_probe_blocked": network_blocked,
                        "no_inference_key": "OPENROUTER_API_KEY" not in os.environ,
                        "no_docker_socket": not Path("/var/run/docker.sock").exists()}
(output / "verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
(output / "reward.txt").write_text("1\n" if verdict["complete"] else "0\n")
