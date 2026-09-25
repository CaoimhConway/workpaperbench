"""Run one native Harbor trial inside the dedicated local Linux guest."""
import argparse
import asyncio
import base64
from datetime import datetime, timezone
import hashlib
import fcntl
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from workpaperbench.catalog import load, tree_hash
from fresh_replay import ensure_no_symlink_ancestors, parse_json, read_bounded, reject_credential_patterns
from fix_native_version import corrected_hermes_source


def clean_environment():
    allowed = {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "PYTHONUNBUFFERED"}
    for name in list(os.environ):
        if name not in allowed:
            del os.environ[name]
    if platform.system() != "Linux" or not Path("/etc/workpaperbench-local-profile").is_file():
        raise ValueError("local_trial_requires_dedicated_guest")


def local_hermes_source(source, max_turns, generation=None, system_prompt=""):
    corrected = corrected_hermes_source(source)
    installers = re.findall(rb'https://raw\.githubusercontent\.com/[^/\s]+/hermes-agent/main/scripts/install\.sh', corrected)
    if len(installers) != 1:
        raise ValueError('local_installer_revision_anchor')
    installer = installers[0]
    corrected = corrected.replace(b'curl -fsSL ' + installer + b' | bash -s --',
        b'bash /opt/workpaperbench-runtime/hermes-install.sh')
    install_environment = b'"set -euo pipefail; "\n'
    if corrected.count(install_environment) != 1:
        raise ValueError('local_install_environment_anchor')
    corrected = corrected.replace(install_environment,
        b'\'set -euo pipefail; export HERMES_HOME="/tmp/hermes" HERMES_INSTALL_DIR="/tmp/hermes/hermes-agent"; apt-get update && apt-get install -y sqlite3; \'\n')
    corrected = corrected.replace(b'--skip-setup{branch_flag}', b'--skip-setup --skip-browser --skip-computer-use{branch_flag}')
    warmup = b'                "hermes --version"\n'
    if corrected.count(warmup) != 1:
        raise ValueError('local_cli_warmup_anchor')
    corrected = corrected.replace(warmup, b'                "hermes --version && hermes chat --help && hermes pm env npm"\n')
    before = b'_NATIVE_PROVIDERS: dict[str, tuple[str | None, list[str]]] = {\n'
    if corrected.count(before) != 1:
        raise ValueError("local_native_provider_anchor")
    corrected = corrected.replace(before, before + b'    "custom": ("custom", ["OPENAI_API_KEY"]),\n')
    corrected = corrected.replace(b'if use_native and provider == "openai":', b'if use_native and provider in ("openai", "custom"):')
    before = b'        config_yaml = self._build_config_yaml(cli_model)\n'
    generation = generation or {'max_tokens': 2048, 'temperature': 0.6, 'top_p': 0.95, 'top_k': 20, 'seed': 17}
    block = '''        if provider != "custom" or env.get("OPENAI_API_KEY") != "local-only":
            raise ValueError("Local profile requires its credential-free custom route")
        if env.get("OPENAI_BASE_URL") != "http://172.17.0.1:18080/v1":
            raise ValueError("Unexpected local model endpoint")
        local_config = yaml.safe_load(self._build_config_yaml(cli_model))
        route = {"default": model, "provider": "custom", "base_url": env["OPENAI_BASE_URL"],
                 "api_key": "local-only", "api_mode": "chat_completions"}
        local_config["model"] = route
        local_config["custom_providers"] = [{"name": "workpaperbench-local", "base_url": env["OPENAI_BASE_URL"],
            "api_key": "local-only", "model": model, "context_length": CONTEXT_LENGTH, "extra_body": GENERATION}]
        local_config["provider"] = "custom"
        local_config["fallback_model"] = None
        local_config["agent"]["max_turns"] = MAX_TURNS
        local_config["agent"]["system_prompt"] = SYSTEM_PROMPT
        local_config["compression"]["enabled"] = False
        local_config["auxiliary"] = {"title_generation": {"enabled": False, "model_upgrade_enabled": False}}
        for role in ("vision", "compression", "approval", "review", "skills_hub", "mcp"):
            local_config["auxiliary"][role] = {"provider": "custom", "model": model,
                "base_url": env["OPENAI_BASE_URL"], "api_key": "local-only", "api_mode": "chat_completions"}
        config_yaml = yaml.dump(local_config, default_flow_style=False)
'''.replace("MAX_TURNS", str(max_turns)).replace('SYSTEM_PROMPT', repr(system_prompt)).replace('CONTEXT_LENGTH', str(generation.pop('_context', 16384))).replace('GENERATION', repr(generation)).encode()
    if corrected.count(before) != 1:
        raise ValueError("local_native_config_anchor")
    return corrected.replace(before, block)


async def run(arguments):
    clean_environment()
    (ROOT / '.local').mkdir(exist_ok=True)
    trial_lock = (ROOT / '.local/local-trial.lock').open('a')
    try:
        fcntl.flock(trial_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        raise ValueError('another_local_trial_is_running') from error
    manifest, spec, source = load(ROOT, arguments.dataset, arguments.task)
    configuration = None
    if arguments.configuration:
        config_bytes = read_bounded(arguments.configuration, 20000)
        configuration = parse_json(config_bytes)
        if (configuration['model']['id'] != arguments.model
                or configuration['execution_profile'] != 'local-lima'
                or configuration['candidate']['turns'] != arguments.turns
                or configuration['candidate']['wall_seconds'] != arguments.wall):
            raise ValueError('effective_model_configuration_mismatch')
    output = ROOT / ".raw/local-trials" / arguments.attempt
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    receipt = {"attempt_id": arguments.attempt, "execution_profile": "local-lima",
               "manifest_id": manifest["manifest_id"], "task_id": spec["task_id"],
               "task_sha256": spec["task_sha256"], "scorer_version": manifest["scorer_version"],
               "scorer_sha256": manifest["scorer_sha256"], "started_at": started,
               "external_service_spend_usd": 0, "status": "started", "inference": arguments.model is not None}
    receipt['execution_files_sha256'] = {name:hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in ('scripts/local_trial.py','scripts/fresh_replay.py','scripts/fix_native_version.py','scripts/native_run.py','config/runtime.json')}
    if configuration:
        receipt['model_configuration'] = configuration
        receipt['model_configuration_sha256'] = hashlib.sha256(config_bytes).hexdigest()
    (output / "start.json").write_text(json.dumps(receipt, indent=2) + "\n")
    task = output / "task"
    # Fresh file metadata avoids reusing a context checksum for equal-sized
    # SQLite files retained with the same original archive timestamps.
    shutil.copytree(source, task, copy_function=shutil.copy)
    if arguments.legacy:
        if arguments.model or arguments.dataset != 'challenge-v2':
            raise ValueError('legacy_replay_is_inference_free')
        canonical_gold = parse_json((task / 'tests/gold.json').read_bytes())
        shutil.rmtree(task)
        legacy_source = ROOT / 'datasets/challenge-v1/tasks' / arguments.task
        shutil.copytree(legacy_source, task, copy_function=shutil.copy,
                        ignore=shutil.ignore_patterns('__pycache__','*.pyc','._*'))
        if tree_hash(task) != spec['origin_task_sha256']:
            raise ValueError('legacy_source_dossier_changed')
        gold = parse_json((task / 'tests/gold.json').read_bytes())
        for identifier, declaration in gold['answers'].items():
            declaration['evidence'] = canonical_gold['answers'][identifier]['evidence']
        if gold.get('conclusion') is not None:
            gold['conclusion']['evidence'] = canonical_gold['conclusion']['evidence']
        gold['scorer_version'] = manifest['scorer_version']
        shutil.copyfile(source / 'tests/workpaperbench/challenge_grading.py', task / 'tests/workpaperbench/challenge_grading.py')
        shutil.copyfile(source / 'tests/verify.py', task / 'tests/verify.py')
        gold['hashes']['verify.py'] = hashlib.sha256((task / 'tests/verify.py').read_bytes()).hexdigest()
        (task / 'tests/gold.json').write_text(json.dumps(gold,indent=2) + '\n')
        toml = task / 'task.toml'
        toml.write_text(toml.read_text().replace('allowed_hosts = ["openrouter.ai"]', 'allowed_hosts = ["172.17.0.1"]'))
        receipt.update(task_id=gold['task_id'], source_task_sha256=spec['origin_task_sha256'],
                       source_snapshot='challenge-v1 original published candidate dossier',
                       historical_inputs_repaired=False)
    if arguments.model:
        installer_path = ROOT / '.local/hermes-install.sh'
        installer_bytes = read_bounded(installer_path, 100000)
        receipt['hermes_installer_sha256'] = hashlib.sha256(installer_bytes).hexdigest()
        (task / 'environment/hermes-install.sh').write_bytes(installer_bytes)
        dockerfile = task / 'environment/Dockerfile'
        dockerfile.write_text(dockerfile.read_text() + 'COPY hermes-install.sh /opt/workpaperbench-runtime/hermes-install.sh\n')
    if arguments.answer:
        answer = read_bounded(arguments.answer, 65536)
        reject_credential_patterns(answer)
        encoded = base64.b64encode(answer).decode()
        (task / "solution/solve.sh").write_text(
            "#!/bin/bash\nset -euo pipefail\npython - <<'WRITE'\n"
            "import base64\nfrom pathlib import Path\n"
            "Path('/logs/artifacts/answer.json').write_bytes(base64.b64decode(" + repr(encoded) + "))\nWRITE\n")
    if arguments.artifacts:
        directory = arguments.artifacts
        if directory.is_symlink() or not directory.is_dir() or len(list(directory.iterdir())) > 5:
            raise ValueError('unsafe_submission_directory')
        script = "#!/bin/bash\nset -euo pipefail\npython - <<'WRITE'\nimport base64\nfrom pathlib import Path\n"
        for path in sorted(directory.iterdir()):
            if path.name != 'answer.json' and not __import__('re').fullmatch(r'[a-z][a-z0-9_]{0,40}\.sql', path.name):
                raise ValueError('unsafe_submission_name')
            raw = read_bounded(path, 65536 if path.name == 'answer.json' else 16384)
            reject_credential_patterns(raw)
            script += "Path('/logs/artifacts/" + path.name + "').write_bytes(base64.b64decode(" + repr(base64.b64encode(raw).decode()) + "))\n"
        (task / 'solution/solve.sh').write_text(script + 'WRITE\n')
    if arguments.boundaries:
        original_solution = (task / "solution/solve.sh").read_text()
        probe = '''python - <<'BOUNDARIES'
import json, socket
from pathlib import Path
checks = {}
for name in ('/tests/gold.json', '/workspace/.git', '/Users', '/root/.ssh', '/var/run/docker.sock'):
    checks['unavailable:' + name] = not Path(name).exists()
checks['fresh_candidate_state'] = not Path('/workspace/local-state-probe').exists()
Path('/workspace/local-state-probe').write_text('one trial only')
for host, port, label in [('1.1.1.1',443,'external_tls'), ('172.17.0.1',22,'guest_ssh'), ('172.17.0.1',2375,'daemon_tcp')]:
    try:
        with socket.create_connection((host, port),timeout=2): pass
        checks[label + '_blocked'] = False
    except OSError:
        checks[label + '_blocked'] = True
for host, port, label in [('1.1.1.1',53,'external_dns_udp'),('127.0.0.11',53,'docker_dns_stub')]:
    probe=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    probe.settimeout(2)
    try:
        probe.sendto(bytes.fromhex('aabb01000001000000000000076578616d706c6503636f6d0000010001'),(host,port))
        probe.recvfrom(512)
        checks[label+'_blocked']=False
    except OSError:
        checks[label+'_blocked']=True
    finally:
        probe.close()
checks['icmp_probe_available'] = False
try:
    probe=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_ICMP)
    checks['icmp_probe_available'] = True
    probe.settimeout(2)
    probe.sendto(bytes.fromhex('0800f7fd00010001'),('1.1.1.1',0))
    probe.recvfrom(512)
    checks['external_icmp_blocked'] = False
except OSError:
    checks['external_icmp_blocked'] = True
finally:
    if checks['icmp_probe_available']: probe.close()
Path('/workspace/data.sqlite').write_bytes(b'candidate overwrite must not reach pristine verification')
Path('/workspace/local-boundaries.json').write_text(json.dumps(checks))
assert all(checks.values()), checks
BOUNDARIES
'''
        (task / "solution/solve.sh").write_text(original_solution.replace('set -euo pipefail\n', 'set -euo pipefail\n' + probe, 1))
    receipt['effective_task_sha256'] = tree_hash(task)
    try:
        from harbor.models.trial.config import TrialConfig
        from harbor.trial.trial import Trial
        from harbor.trial.hooks import TrialEvent
        agent = {"name": "oracle", "override_timeout_sec": 120}
        if arguments.model:
            from importlib.metadata import distribution
            distribution_path = distribution("harbor").locate_file("harbor/agents/installed/hermes.py")
            adapter = Path(distribution_path)
            original = adapter.read_bytes()
            if original != (ROOT / ".local/harbor-hermes-original.py").read_bytes():
                raise ValueError("local_native_adapter_changed")
            generation = copy_generation = dict(configuration['candidate']['generation']) if configuration else None
            if copy_generation is not None:
                copy_generation['_context'] = configuration['serving']['context']
            effective = local_hermes_source(original, arguments.turns, generation, configuration["candidate"].get("system_prompt", "") if configuration else "")
            adapter.write_bytes(effective)
            receipt["native_adapter_sha256"] = hashlib.sha256(effective).hexdigest()
            os.environ["OPENAI_API_KEY"] = "local-only"
            os.environ["OPENAI_BASE_URL"] = "http://172.17.0.1:18080/v1"
            agent = {"name": "hermes", "model_name": "custom/" + arguments.model,
                     "override_timeout_sec": arguments.wall, "override_setup_timeout_sec": 1200,
                     "kwargs": {"version": "v0.21.4+canary.20261004T084456Z", "toolsets": configuration["candidate"].get("toolsets", "file,terminal,skills") if configuration else "file,terminal,skills"}}
        config = TrialConfig.model_validate({"task": {"path": str(task)}, "trial_name": arguments.attempt,
                                           "trials_dir": str(output / "trials"), "agent": agent,
                                           "environment": {"type": "docker"}})
        trial = await Trial.create(config)
        async def enforce_local_network(event):
            command = ['docker', 'ps', '--filter', 'label=com.docker.compose.project=' + arguments.attempt + '__env',
                       '--filter', 'label=com.docker.compose.service=harbor-docker-egress-control-sidecar',
                       '--format', '{{.ID}}']
            sidecar = subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
            if not __import__('re').fullmatch(r'[0-9a-f]{12,64}', sidecar):
                raise ValueError('local_egress_sidecar_missing')
            rules = ('add table inet workpaperbench_local\n'
                     'add chain inet workpaperbench_local local_route { type route hook output priority -150; policy accept; }\n'
                     'add rule inet workpaperbench_local local_route ip daddr 172.17.0.1 tcp dport 18080 meta mark set 114514\n'
                     'add chain inet workpaperbench_local output { type filter hook output priority 10; policy drop; }\n'
                     'add rule inet workpaperbench_local output ip daddr 127.0.0.11 counter drop\n'
                     'add rule inet workpaperbench_local output meta l4proto { icmp, ipv6-icmp } counter drop\n'
                     'add rule inet workpaperbench_local output oifname "lo" accept\n'
                     'add rule inet workpaperbench_local output ip daddr 172.17.0.1 tcp dport 18080 accept\n'
                     'add rule inet workpaperbench_local output counter drop\n')
            subprocess.run(['docker', 'exec', '-i', sidecar, 'nft', '-f', '-'], input=rules,
                           capture_output=True, text=True, timeout=10, check=True)
            receipt['candidate_network_policy'] = 'Loopback and guest bridge TCP 18080 only, all other IPv4/IPv6 protocols dropped'
            if arguments.model:
                health = await trial.agent_environment.exec(
                    command='curl --fail --silent --connect-timeout 5 --max-time 10 http://172.17.0.1:18080/v1/models', timeout_sec=12)
                if health.return_code:
                    raise ValueError('candidate_local_model_route_unavailable')
                models = parse_json(health.stdout)
                if arguments.model not in [item['id'] for item in models['data']]:
                    raise ValueError('candidate_local_model_identity_changed')
                receipt['candidate_local_model_health'] = True
        trial.add_hook(TrialEvent.AGENT_START, enforce_local_network)
        if arguments.boundaries:
            async def retain_boundaries(event):
                probe = await trial.agent_environment.exec(command="cat /workspace/local-boundaries.json", timeout_sec=10)
                receipt['candidate_boundary_checks'] = parse_json(probe.stdout)
            trial.add_hook(TrialEvent.AGENT_END, retain_boundaries)
        if arguments.model:
            async def check_version(event):
                result = await trial.agent_environment.exec(
                    command="git -C /tmp/hermes/hermes-agent rev-parse HEAD", timeout_sec=10)
                if result.return_code or result.stdout.strip() != "8b66a51036c1e20920a17cdd049fdf55c968d683":
                    raise ValueError("local_hermes_revision_mismatch")
            trial.add_hook(TrialEvent.AGENT_START, check_version)
        result = await trial.run()
        if result.exception_info is not None:
            raise RuntimeError(result.exception_info.exception_message)
        verifier = output / "trials" / arguments.attempt / "verifier/verdict.json"
        raw = read_bounded(verifier, 100000)
        verdict = parse_json(raw)
        if not all(verdict.get("isolation", {}).values()) or len(verdict.get("isolation", {})) != 4:
            raise ValueError("local_verifier_boundary_failed")
        receipt.update(status="verified", verdict=verdict, verdict_sha256=hashlib.sha256(raw).hexdigest())
        (output / "verifier.json").write_bytes(raw)
    except asyncio.CancelledError:
        receipt.update(status='cancelled', error='Local trial cancelled before a completed verifier receipt')
        raise
    except Exception as error:
        receipt.update(status="infrastructure_failed", error=str(error)[:500], error_type=type(error).__name__)
        raise
    finally:
        try:
            artifact = output / "trials" / arguments.attempt / "artifacts/logs/artifacts/answer.json"
            if artifact.exists() or artifact.is_symlink():
                artifact = ensure_no_symlink_ancestors(artifact, ROOT)
                answer = read_bounded(artifact, 65536)
                reject_credential_patterns(answer)
                (output / "raw-answer.json").write_bytes(answer)
                receipt["raw_answer_sha256"] = hashlib.sha256(answer).hexdigest()
                if arguments.dataset.startswith('workflow-'):
                    receipt['sql_file_sha256'] = {}
                    raw_sql = output / 'raw-sql'
                    raw_sql.mkdir()
                    for path in sorted(artifact.parent.iterdir()):
                        if path.name == 'answer.json':
                            continue
                        if not __import__('re').fullmatch(r'[a-z][a-z0-9_]{0,40}\.sql', path.name):
                            raise ValueError('unsafe_retained_sql_name')
                        path = ensure_no_symlink_ancestors(path, ROOT)
                        data = read_bounded(path, 16384)
                        reject_credential_patterns(data)
                        (raw_sql / path.name).write_bytes(data)
                        receipt['sql_file_sha256'][path.name] = hashlib.sha256(data).hexdigest()
                try:
                    normalized = (json.dumps(parse_json(answer), indent=2, allow_nan=False) + "\n").encode()
                    (output / "answer.json").write_bytes(normalized)
                    receipt["normalized_answer_sha256"] = hashlib.sha256(normalized).hexdigest()
                except ValueError:
                    receipt["normalized_answer_sha256"] = None
        except Exception as error:
            receipt["retention_error"] = str(error)[:500]
            raise
        finally:
            if arguments.model and 'original' in locals():
                adapter.write_bytes(original)
            receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
            (output / "receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="challenge-v2")
    parser.add_argument("--task", default="c03")
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--answer", type=Path)
    parser.add_argument('--artifacts', type=Path)
    parser.add_argument('--legacy', action='store_true')
    parser.add_argument("--model")
    parser.add_argument('--configuration', type=Path)
    parser.add_argument("--boundaries", action="store_true")
    parser.add_argument("--wall", type=int, default=600)
    parser.add_argument("--turns", type=int, default=12)
    args = parser.parse_args()
    if not __import__('re').fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}", args.attempt):
        raise SystemExit("Invalid attempt ID")
    asyncio.run(run(args))
