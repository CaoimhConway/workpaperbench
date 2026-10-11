"""Bounded IPv6 transport control test using trusted containers, without inference."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from local_trial import endpoint_rules

SERVER = '''import socket,threading,time
def listen(port):
    server=socket.socket(socket.AF_INET6,socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    server.bind(('::',port))
    server.listen()
    while True:
        connection,_=server.accept()
        with connection:
            connection.recv(32)
            connection.sendall(b'ipv6-fixture')
for port in (28443,28444):
    threading.Thread(target=listen,args=(port,),daemon=True).start()
time.sleep(0.2)
print('READY',flush=True)
while True: time.sleep(1)
'''

PROBE = '''import json,socket,sys
address=sys.argv[1]
result={}
for port in (28443,28444):
    try:
        with socket.create_connection((address,port),timeout=2) as client:
            client.sendall(b'probe')
            result[str(port)]=client.recv(32)==b'ipv6-fixture'
    except OSError:
        result[str(port)]=False
try:
    with socket.socket(socket.AF_INET6,socket.SOCK_DGRAM,socket.IPPROTO_ICMPV6) as client:
        client.settimeout(2)
        client.sendto(bytes.fromhex('8000000000010001')+b'fixture',(address,0,0,0))
        result['echo']=client.recv(1024)[0]==129
except OSError:
    result['echo']=False
print(json.dumps(result))
'''


def docker(*arguments, **kwargs):
    return subprocess.run(['docker', *arguments], check=True, capture_output=True,
                          text=True, timeout=30, **kwargs).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-image', required=True)
    parser.add_argument('--sidecar-image', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('proof_already_exists')
    identifier = uuid.uuid4().hex[:10]
    network = 'wpb-ipv6-' + identifier
    sidecar, server = network + '-client', network + '-server'
    prefix = 'fd' + identifier[:2] + ':' + identifier[2:6] + ':' + identifier[6:] + ':1'
    address = prefix + '::10'
    endpoint = {'hostname': address, 'addresses': [address], 'port': 28443}
    rules = endpoint_rules(endpoint)
    proof = {'kind': 'trusted_ipv6_network_fixture', 'inference': False,
             'external_service_spend_usd': 0, 'passed': False,
             'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'runner_sha256': hashlib.sha256((ROOT / 'scripts/local_trial.py').read_bytes()).hexdigest(),
             'rules_sha256': hashlib.sha256(rules.encode()).hexdigest()}
    created = []
    try:
        proof['images'] = {name: json.loads(docker('image', 'inspect', image))[0]['Id']
                           for name, image in [('python', args.python_image), ('native_sidecar', args.sidecar_image)]}
        docker('network', 'create', '--internal', '--ipv6', '--subnet', prefix + '::/64', network)
        created.append(('network', network))
        docker('run', '-d', '--pull=never', '--name', server, '--network', network, '--ip6', address,
               '--read-only', '--memory', '128m', '--cpus', '0.5', '--pids-limit', '16',
               '--cap-drop', 'ALL', '--entrypoint', 'python', args.python_image, '-c', SERVER)
        created.append(('container', server))
        docker('run', '-d', '--pull=never', '--name', sidecar, '--network', network,
               '--memory', '128m', '--cpus', '0.5', '--pids-limit', '32',
               '--cap-add', 'NET_ADMIN', '--cap-add', 'NET_RAW',
               '-e', 'EGRESS_CONTROL_INITIAL_NETWORK_MODE=public',
               '--entrypoint', '/opt/egress-sidecar/entrypoint.sh', args.sidecar_image)
        created.append(('container', sidecar))
        for _ in range(15):
            if 'READY' in docker('logs', server) and 'ready:' in docker('logs', sidecar):
                break
            time.sleep(1)
        else:
            raise ValueError('fixture_container_not_ready')

        def probe():
            return json.loads(docker('run', '--rm', '--pull=never', '--network', 'container:' + sidecar,
                '--read-only', '--memory', '128m', '--cpus', '0.5', '--pids-limit', '16',
                '--cap-drop', 'ALL', '--cap-add', 'NET_RAW', '--entrypoint', 'python',
                args.python_image, '-c', PROBE, address))

        proof['before_policy'] = probe()
        if proof['before_policy'] != {'28443': True, '28444': True, 'echo': True}:
            raise ValueError('ipv6_transport_not_available_before_policy')
        docker('exec', sidecar, 'network-policy', 'allow', address)
        docker('exec', '-i', sidecar, 'nft', '-f', '-', input=rules)
        docker('exec', sidecar, 'ip', '-6', 'neigh', 'flush', 'all')
        proof['fresh_neighbors'] = address not in docker('exec', sidecar, 'ip', '-6', 'neigh', 'show')
        proof['after_policy'] = probe()
        proof['rules_verified'] = 'nd-neighbor-solicit' in docker('exec', sidecar, 'nft', 'list', 'table', 'inet', 'workpaperbench_local')
        proof['passed'] = (proof['fresh_neighbors'] and proof['rules_verified']
                           and proof['after_policy'] == {'28443': True, '28444': False, 'echo': False})
        if not proof['passed']:
            raise ValueError('ipv6_endpoint_policy_failed')
    except Exception as error:
        proof['error_type'] = type(error).__name__
        proof['error'] = str(error)[:500]
    finally:
        failures = []
        for kind, name in reversed(created):
            try:
                docker('rm', '-f', name) if kind == 'container' else docker('network', 'rm', name)
            except Exception:
                failures.append(name)
        proof['cleanup_complete'] = not failures
        if failures:
            proof['cleanup_failures'] = failures
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as output:
            output.write(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof, indent=2))
    if not proof['passed'] or not proof['cleanup_complete']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
