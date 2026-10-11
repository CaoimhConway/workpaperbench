"""Exercise authenticated HTTPS through native Hermes without model inference."""
import argparse
import asyncio
from functools import partial
import hashlib
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import shlex
import ssl
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import guest_bench
import local_trial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--port', type=int, default=19443)
    args = parser.parse_args()
    guest_bench.preflight()
    from harbor.trial.trial import Trial
    from harbor.trial.hooks import TrialEvent
    hostname = 'workpaperbench-fixture.test'
    bridge = json.loads(subprocess.check_output(['docker', 'network', 'inspect', 'bridge'], text=True))
    address = bridge[0]['IPAM']['Config'][0]['Gateway']
    credential = 'fixture-only-no-provider-credential'
    spec = json.loads((ROOT / 'config/external-model.example.json').read_text())
    spec.update(configuration_id='authenticated-https-native-fixture-1',
                model={'id': 'deterministic-harness-fixture', 'revision': 'scripted-no-inference'},
                runtime={'name': 'Python standard-library TLS fixture', 'version': '1'})
    spec['serving'].update(base_url=f'https://{hostname}:{args.port}/v1', api_key_env='WPB_FIXTURE_API_KEY')
    spec['candidate'].update(turns=3, wall_seconds=180)
    profile = ROOT / '.local' / (args.attempt + '-https-profile.json')
    with profile.open('x') as stream:
        stream.write(json.dumps(spec, indent=2) + '\n')
    observations = []
    original_create, original_resolve = Trial.create, local_trial.resolve_endpoint
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        certificate, key = directory / 'certificate.pem', directory / 'private-key.pem'
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                        '-subj', '/CN=' + hostname, '-addext', 'subjectAltName=DNS:' + hostname,
                        '-keyout', str(key), '-out', str(certificate)], check=True, capture_output=True)
        ca_bytes = certificate.read_bytes()
        async def create(config):
            trial = await original_create(config)
            async def trust_fixture_certificate(event):
                command = 'printf %s ' + shlex.quote(ca_bytes.decode()) + ' > /tmp/wpb-fixture-ca.pem'
                result = await trial.agent_environment.exec(command=command, timeout_sec=10)
                if result.return_code:
                    raise ValueError('fixture_certificate_install_failed')
                trial.agent_environment._persistent_env['SSL_CERT_FILE'] = '/tmp/wpb-fixture-ca.pem'
            trial.add_hook(TrialEvent.AGENT_START, trust_fixture_certificate)
            return trial
        def resolve(value):
            if value == spec['serving']['base_url']:
                return {'hostname': hostname, 'port': args.port, 'addresses': [address]}
            return original_resolve(value)
        Trial.create, local_trial.resolve_endpoint = create, resolve
        server = ThreadingHTTPServer((address, args.port), partial(guest_bench.FixtureHandler,
                                      observations=observations, credential=credential))
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certificate, key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            arguments = argparse.Namespace(dataset='workflow-v8', task='c09', attempt=args.attempt)
            asyncio.run(local_trial.run(guest_bench.trial_arguments(arguments, profile, smoke=True), credential=credential))
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)
            Trial.create, local_trial.resolve_endpoint = original_create, original_resolve
    output = ROOT / '.raw/local-trials' / args.attempt
    receipt = json.loads((output / 'receipt.json').read_text())
    passed = (receipt['status'] == 'verified' and receipt['inference'] is False
              and receipt['verdict']['checks']['delivery'] is False
              and (output / 'raw-answer.json').read_bytes() == b'{}'
              and len(observations) == 2 and observations[-1]['tool_result_observed']
              and all(row['generation'] == spec['candidate']['generation'] for row in observations))
    proof = {'kind': 'scripted_authenticated_https_native_fixture', 'inference': False,
             'financial_evaluation': False, 'passed': passed, 'requests': observations,
             'certificate_verification': 'Native client verification enabled, fixture CA supplied through candidate SSL_CERT_FILE after native setup',
             'dns_fixture': 'Test-only mapping of workpaperbench-fixture.test to Docker bridge. Normal runner pins that hostname in candidate hosts.',
             'certificate_sha256': hashlib.sha256(ca_bytes).hexdigest(),
             'fixture_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'runner_sha256': hashlib.sha256((ROOT / 'scripts/local_trial.py').read_bytes()).hexdigest(),
             'endpoint': spec['serving']['base_url']}
    (output / 'https-smoke.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof, indent=2))
    if not passed:
        raise SystemExit('HTTPS native fixture failed')


if __name__ == '__main__':
    main()
