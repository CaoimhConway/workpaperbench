"""One fixed-window public USDC acquisition with six requests per source path."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen

ADDRESS = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ENDPOINTS = ["https://ethereum-rpc.publicnode.com", "https://cloudflare-eth.com/v1/mainnet"]
FIRST, LAST = 20000000, 20000031


def acquire(endpoint, counts):
    count = 0

    def rpc(method, params):
        nonlocal count
        count += 1
        counts[endpoint] = count
        if count > 6:
            raise RuntimeError("request budget exhausted")
        body = json.dumps({"jsonrpc": "2.0", "id": count, "method": method, "params": params}).encode()
        request = Request(endpoint, body, {"Content-Type": "application/json", "User-Agent": "WorkpaperBench/0.1"})
        with urlopen(request, timeout=45) as response:
            data = json.load(response)
        if "error" in data:
            raise RuntimeError("RPC error")
        time.sleep(1)
        return data["result"]

    logs = rpc("eth_getLogs", [{"fromBlock": hex(FIRST), "toBlock": hex(LAST), "address": ADDRESS, "topics": [TOPIC]}])
    chain = rpc("eth_chainId", [])
    start = rpc("eth_getBlockByNumber", [hex(FIRST), False])
    finish = rpc("eth_getBlockByNumber", [hex(LAST), False])
    decimals = rpc("eth_call", [{"to": ADDRESS, "data": "0x313ce567"}, hex(LAST)])
    code = rpc("eth_getCode", [ADDRESS, hex(LAST)])
    if int(chain, 16) != 1 or int(decimals, 16) != 6 or len(code) <= 2:
        raise ValueError("contract metadata mismatch")
    if int(start["number"], 16) != FIRST or int(finish["number"], 16) != LAST or int(start["timestamp"], 16) > int(finish["timestamp"], 16):
        raise ValueError("boundary metadata mismatch")
    identities = set()
    amount_sum = 0
    for log in logs:
        identity = (log["blockHash"], log["logIndex"])
        if identity in identities or log.get("removed") or log["address"].lower() != ADDRESS:
            raise ValueError("invalid log identity")
        identities.add(identity)
        if not FIRST <= int(log["blockNumber"], 16) <= LAST or len(log["topics"]) != 3 or log["topics"][0] != TOPIC or len(log["data"]) != 66:
            raise ValueError("invalid Transfer encoding")
        if any(not re.fullmatch(r"0x0{24}[0-9a-fA-F]{40}", topic) for topic in log["topics"][1:]):
            raise ValueError("invalid address topic encoding")
        if any(not re.fullmatch(r"0x[0-9a-fA-F]{64}", log[name]) for name in ("blockHash", "transactionHash")):
            raise ValueError("invalid hash encoding")
        amount_sum += int(log["data"], 16)
    if amount_sum >= 2**63:
        raise ValueError("SQLite integer sum exceeds bound")
    return {"origin": "observed_public_rpc", "endpoint": endpoint, "requests": count,
            "chain_id": 1, "first_block": FIRST, "last_block": LAST, "contract": ADDRESS,
            "decimals": 6, "topic0": TOPIC, "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "boundary_headers": [{k: head[k] for k in ("number", "hash", "parentHash", "timestamp")} for head in (start, finish)],
            "code_sha256": hashlib.sha256(bytes.fromhex(code[2:])).hexdigest(), "logs": logs,
            "logs_sha256": hashlib.sha256(json.dumps(logs, sort_keys=True).encode()).hexdigest()}


if __name__ == "__main__":
    destination = Path("capture")
    destination.mkdir(exist_ok=True)
    failures = []
    counts = {}
    for endpoint in ENDPOINTS:
        try:
            result = acquire(endpoint, counts)
            result["failed_paths"] = failures
            (destination / "log_capture.json").write_text(json.dumps(result, indent=2) + "\n")
            print("Captured", len(result["logs"]), "Transfer logs in the fixed window")
            break
        except Exception as exc:
            failures.append({"endpoint": endpoint, "requests": counts.get(endpoint, 0), "error": type(exc).__name__})
            time.sleep(5)
    else:
        (destination / "failure.json").write_text(json.dumps(failures, indent=2) + "\n")
        print("Both bounded acquisition paths failed. Synthetic downgrade required.")
