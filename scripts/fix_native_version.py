"""Correct pinned native CLI version, OpenRouter routing and session export."""
import hashlib
from importlib.metadata import distribution
import os
from pathlib import Path

if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_OS") != "Linux":
    raise SystemExit("Native dependency correction runs only on hosted Actions")
package = distribution("harbor")
if package.version != "0.23.0":
    raise SystemExit("Unexpected Harbor version")
path = Path(package.locate_file("harbor/agents/installed/hermes.py"))
source = path.read_bytes()
if hashlib.sha256(source).hexdigest() != "012e980302b26641dcf77f31fe71a368b2022b098619853addd015c5e18e47c6":
    raise SystemExit("Pinned native source mismatch")
corrected = source.replace(b"hermes version", b"hermes --version")
original_route = b'            env["OPENROUTER_API_KEY"] = openrouter_key\n'
corrected = corrected.replace(original_route, original_route +
    b'            if provider == "openrouter":\n                hermes_provider_flag = "openrouter"\n')
corrected = corrected.replace(b"--source cli 2>/dev/null", b"--source oneshot 2>/dev/null")
digest = hashlib.sha256(corrected).hexdigest()
if digest != "02ebd73edb387091480df45fdea27b70bf37ca377ee0b68047b84d6cdbede112":
    raise SystemExit("Native correction mismatch")
path.write_bytes(corrected)
print("Native Hermes CLI compatibility corrected", digest)
