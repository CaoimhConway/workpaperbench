"""Correct two obsolete version invocations in the pinned native adapter."""
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
digest = hashlib.sha256(corrected).hexdigest()
if digest != "c80026a637135f3accfbc1534f77767f65269a0fcbbdc094355af3a8af5d498e":
    raise SystemExit("Native correction mismatch")
path.write_bytes(corrected)
print("Native Hermes version flag corrected", digest)
