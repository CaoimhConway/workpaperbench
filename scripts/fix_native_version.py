"""Correct pinned native CLI version, routing, session export and observer config."""
import hashlib
import os
from pathlib import Path


ORIGINAL_MODULE_SHA256 = "012e980302b26641dcf77f31fe71a368b2022b098619853addd015c5e18e47c6"
CORRECTED_MODULE_SHA256 = "9aa3157ba2fc1aff3a11a8ec833bbc3eb01506630ffd962e124cf39e362db5e7"


def add_retry_observer_config(source):
    config_builder = b"        config_yaml = self._build_config_yaml(cli_model)\n"
    if source.count(config_builder) != 1:
        raise SystemExit("Pinned native config builder mismatch")
    observer_config = (
        b'        if self._extra_env.get("WPB_NATIVE_RETRY_LEDGER"):\n'
        b'            config_yaml += "\\nplugins:\\n  enabled:\\n    - native-api-observer\\n"\n'
    )
    return source.replace(config_builder, config_builder + observer_config)


def corrected_hermes_source(source):
    """Patch only the exact pinned adapter and conditionally retain the observer."""
    if hashlib.sha256(source).hexdigest() != ORIGINAL_MODULE_SHA256:
        raise SystemExit("Pinned native source mismatch")

    corrected = source.replace(b"hermes version", b"hermes --version")
    original_route = b'            env["OPENROUTER_API_KEY"] = openrouter_key\n'
    corrected = corrected.replace(original_route, original_route +
        b'            if provider == "openrouter":\n                hermes_provider_flag = "openrouter"\n')
    corrected = corrected.replace(b"--source cli 2>/dev/null", b"--source oneshot 2>/dev/null")

    return add_retry_observer_config(corrected)


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_OS") != "Linux":
        raise SystemExit("Native dependency correction runs only on hosted Actions")
    from importlib.metadata import distribution

    package = distribution("harbor")
    if package.version != "0.23.0":
        raise SystemExit("Unexpected Harbor version")
    path = Path(package.locate_file("harbor/agents/installed/hermes.py"))
    source = path.read_bytes()
    corrected = corrected_hermes_source(source)
    digest = hashlib.sha256(corrected).hexdigest()
    if digest != CORRECTED_MODULE_SHA256:
        raise SystemExit("Native correction mismatch")
    path.write_bytes(corrected)
    print("Native Hermes CLI compatibility corrected", digest)


if __name__ == "__main__":
    main()
