#!/usr/bin/env python3
"""Capture first-page Bitcoin transactions around the 2024 block subsidy halving."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "datasets" / "real-v1" / "captures" / "bitcoin-halving"
API_BASE = "https://blockstream.info/api"
API_DOCUMENTATION = "https://github.com/Blockstream/esplora/blob/bb2d9f37bdb0eb0dade45b121a1df3581d7443ea/API.md"
TERMS_URL = "https://blockstream.com/terms/"
HALVING_HEIGHT = 840_000
PRE_HEIGHT = HALVING_HEIGHT - 1
PAGE_START = 0
PAGE_SIZE = 25
SATOSHIS_PER_BTC = 100_000_000
INITIAL_SUBSIDY_SATS = 50 * SATOSHIS_PER_BTC
HALVING_INTERVAL = 210_000
MAX_RESPONSE_BYTES = 2_000_000


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def fetch(path: str, expect_json: bool = True) -> tuple[bytes, object]:
    request = Request(
        f"{API_BASE}{path}",
        headers={"User-Agent": "WorkpaperBench-source-review/1.0"},
        method="GET",
    )
    with urlopen(request, timeout=20) as response:
        content = response.read(MAX_RESPONSE_BYTES + 1)
        content_type = response.headers.get("content-type", "")
    if len(content) > MAX_RESPONSE_BYTES:
        raise RuntimeError(f"Response exceeded {MAX_RESPONSE_BYTES} bytes: {path}")
    decoded = json.loads(content) if expect_json else content.decode("ascii").strip()
    return content, decoded


def block_subsidy_sats(height: int) -> int:
    halvings = height // HALVING_INTERVAL
    return INITIAL_SUBSIDY_SATS >> halvings


def normalize_block(block: dict[str, object]) -> dict[str, object]:
    fields = ("id", "height", "timestamp", "previousblockhash", "merkle_root", "tx_count")
    return {field: block[field] for field in fields}


def normalize_transaction(tx: dict[str, object], index: int, height: int) -> dict[str, object]:
    inputs = tx.get("vin")
    outputs = tx.get("vout")
    if not isinstance(inputs, list) or not isinstance(outputs, list):
        raise RuntimeError(f"Transaction {index} omitted inputs or outputs")

    coinbase = bool(inputs) and all(
        isinstance(txin, dict) and txin.get("is_coinbase") is True for txin in inputs
    )
    output_values = [int(txout["value"]) for txout in outputs if isinstance(txout, dict)]
    if len(output_values) != len(outputs):
        raise RuntimeError(f"Transaction {index} has an output without a value")

    normalized: dict[str, object] = {
        "page_index": index,
        "txid": tx["txid"],
        "size_bytes": int(tx["size"]),
        "weight_wu": int(tx["weight"]),
        "vsize_vbytes": (int(tx["weight"]) + 3) // 4,
        "is_coinbase": coinbase,
        "output_values_sats": output_values,
        "output_total_sats": sum(output_values),
        "status": tx.get("status"),
    }

    if coinbase:
        subsidy = block_subsidy_sats(height)
        normalized["nominal_subsidy_sats"] = subsidy
        normalized["coinbase_payout_minus_subsidy_sats"] = sum(output_values) - subsidy
    else:
        input_values: list[int] = []
        for txin in inputs:
            if not isinstance(txin, dict):
                raise RuntimeError(f"Transaction {index} has a malformed input")
            prevout = txin.get("prevout")
            if not isinstance(prevout, dict) or "value" not in prevout:
                raise RuntimeError(f"Transaction {index} is missing a prevout value")
            input_values.append(int(prevout["value"]))
        computed_fee = sum(input_values) - sum(output_values)
        source_fee = int(tx["fee"])
        if computed_fee != source_fee:
            raise RuntimeError(
                f"Transaction {index} fee mismatch: input/output calculation {computed_fee}, API {source_fee}"
            )
        vsize = int(normalized["vsize_vbytes"])
        normalized.update(
            {
                "input_values_sats": input_values,
                "fee_sats": computed_fee,
                "fee_rate_sats_per_vbyte": round(computed_fee / vsize, 8),
            }
        )
    return normalized


def load_frozen_capture(capture_dir: Path) -> tuple[list[dict[str, object]], str, str]:
    manifest_path = capture_dir / "bitcoin-halving.manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"Frozen capture is missing {manifest_path.name}: {capture_dir}")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    response_rows = manifest.get("responses")
    if not isinstance(response_rows, list) or len(response_rows) != 5:
        raise SystemExit("Frozen capture manifest must list the five original API responses")
    listed_files = {str(row.get("file")) for row in response_rows if isinstance(row, dict)}
    actual_files = {path.name for path in capture_dir.glob("*.response")}
    if listed_files != actual_files:
        raise SystemExit("Frozen capture response files do not match its manifest")

    pending: list[dict[str, object]] = []
    for row in response_rows:
        if not isinstance(row, dict):
            raise SystemExit("Frozen capture manifest contains a malformed response entry")
        response_path = capture_dir / str(row["file"])
        content = response_path.read_bytes()
        if len(content) != int(row["bytes"]) or sha256(content) != row["sha256"]:
            raise SystemExit(f"Frozen response failed its byte count or SHA256 check: {response_path.name}")
        pending.append(
            {
                "name": response_path.name.removesuffix(".response"),
                "path": row["request_path"],
                "bytes": content,
            }
        )

    normalized_path = capture_dir / str(manifest.get("normalized_file", ""))
    if not normalized_path.is_file():
        raise SystemExit("Frozen capture is missing its normalized file")
    normalized_bytes = normalized_path.read_bytes()
    if sha256(normalized_bytes) != manifest.get("normalized_sha256"):
        raise SystemExit("Frozen normalized file failed its SHA256 check")

    retrieved_at = manifest.get("retrieved_at_utc")
    if not isinstance(retrieved_at, str):
        raise SystemExit("Frozen capture manifest omitted the original retrieval timestamp")
    return pending, retrieved_at, sha256(manifest_bytes)


def capture_response(
    pending: list[dict[str, object]],
    frozen: dict[str, dict[str, object]],
    name: str,
    path: str,
    expect_json: bool = True,
) -> tuple[bytes, object]:
    if frozen:
        item = frozen.get(name)
        if item is None or item.get("path") != path:
            raise RuntimeError(f"Frozen capture does not contain the expected request {path}")
        content = item["bytes"]
        if not isinstance(content, bytes):
            raise RuntimeError(f"Frozen response is not byte content: {name}")
        decoded = json.loads(content) if expect_json else content.decode("ascii").strip()
        return content, decoded

    content, decoded = fetch(path, expect_json=expect_json)
    pending.append({"name": name, "path": path, "bytes": content})
    return content, decoded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--rebuild-from-capture",
        type=Path,
        help="rebuild derived files offline from a frozen capture into a new empty --output-dir",
    )
    args = parser.parse_args()

    pending: list[dict[str, object]] = []
    frozen: dict[str, dict[str, object]] = {}
    source_manifest_sha256: str | None = None
    if args.rebuild_from_capture is not None:
        if args.output_dir is None:
            raise SystemExit("--rebuild-from-capture requires a distinct, empty --output-dir")
        source_dir = args.rebuild_from_capture.resolve()
        output = args.output_dir.resolve()
        if output == source_dir or source_dir in output.parents:
            raise SystemExit("Offline rebuild output must be outside the frozen source directory")
        pending, retrieved_at, source_manifest_sha256 = load_frozen_capture(source_dir)
        frozen = {str(item["name"]): item for item in pending}
        capture_mode = "offline_rebuild_from_frozen_responses"
    else:
        output = (args.output_dir or DEFAULT_OUTPUT).resolve()
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        capture_mode = "bounded_network_capture"

    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit(f"Capture directory is not empty: {output}. Choose a new --output-dir.")

    height_path = f"/block-height/{HALVING_HEIGHT}"
    raw_height, height_hash = capture_response(
        pending, frozen, "block-height-840000", height_path, expect_json=False
    )
    if not isinstance(height_hash, str) or len(height_hash) != 64:
        raise RuntimeError(f"Unexpected block hash for height {HALVING_HEIGHT}")

    post_block_path = f"/block/{height_hash}"
    raw_post_block, post_block = capture_response(pending, frozen, "block-840000", post_block_path)
    if not isinstance(post_block, dict) or int(post_block.get("height", -1)) != HALVING_HEIGHT:
        raise RuntimeError("The block-height lookup did not resolve to block 840,000")
    pre_hash = post_block.get("previousblockhash")
    if not isinstance(pre_hash, str) or len(pre_hash) != 64:
        raise RuntimeError("The halving block omitted its previous block hash")

    pre_block_path = f"/block/{pre_hash}"
    raw_pre_block, pre_block = capture_response(pending, frozen, "block-839999", pre_block_path)
    if not isinstance(pre_block, dict) or int(pre_block.get("height", -1)) != PRE_HEIGHT:
        raise RuntimeError("The previous block was not height 839,999")
    if pre_block.get("id") != pre_hash:
        raise RuntimeError("The previous block response hash did not match the linked hash")

    page_records: list[dict[str, object]] = []
    for height, block in ((PRE_HEIGHT, pre_block), (HALVING_HEIGHT, post_block)):
        block_hash = str(block["id"])
        tx_path = f"/block/{block_hash}/txs/{PAGE_START}"
        _, txs = capture_response(
            pending,
            frozen,
            f"transactions-first25-{height}",
            tx_path,
        )
        if not isinstance(txs, list) or len(txs) != PAGE_SIZE:
            raise RuntimeError(f"Expected {PAGE_SIZE} transactions at page start {PAGE_START} for block {height}")
        if int(block["tx_count"]) < PAGE_SIZE:
            raise RuntimeError(f"Block {height} has fewer transactions than the returned page")
        normalized = [normalize_transaction(tx, index, height) for index, tx in enumerate(txs)]
        coinbase_rows = [tx for tx in normalized if tx["is_coinbase"]]
        if len(coinbase_rows) != 1 or coinbase_rows[0]["page_index"] != 0:
            raise RuntimeError(f"Block {height} page did not begin with exactly one coinbase transaction")
        page_records.append(
            {
                "block": normalize_block(block),
                "page_start_index": PAGE_START,
                "page_transaction_count": len(normalized),
                "page_is_complete_for_block": int(block["tx_count"]) == len(normalized),
                "transactions": normalized,
            }
        )

    record_by_height = {int(item["block"]["height"]): item for item in page_records}
    if record_by_height[HALVING_HEIGHT]["block"]["previousblockhash"] != record_by_height[PRE_HEIGHT]["block"]["id"]:
        raise RuntimeError("Captured blocks are not adjacent")

    response_hashes: list[dict[str, object]] = []
    for item in pending:
        name = str(item["name"])
        content = item["bytes"]
        if not isinstance(content, bytes):
            raise RuntimeError("Internal capture content was not bytes")
        response_path = output / f"{name}.response"
        response_path.write_bytes(content)
        response_hashes.append(
            {
                "file": response_path.name,
                "request_path": item["path"],
                "sha256": sha256(content),
                "bytes": len(content),
            }
        )

    normalized_path = output / "bitcoin-halving-normalized.json"
    normalized_bytes = (json.dumps(page_records, indent=2, sort_keys=True) + "\n").encode("utf-8")
    normalized_path.write_bytes(normalized_bytes)

    manifest = {
        "source": "Bitcoin Mainnet public chain data via Blockstream Esplora",
        "api_base": API_BASE,
        "api_documentation": API_DOCUMENTATION,
        "api_documentation_commit": "bb2d9f37bdb0eb0dade45b121a1df3581d7443ea",
        "terms_reviewed": TERMS_URL,
        "terms_reviewed_on": "2026-10-06",
        "reuse_review": "The Esplora repository is MIT-licensed software, which is not asserted as a license for API data. The public Blockstream terms were reviewed and no separate public API-data redistribution grant was identified. This capture retains a bounded sample of public Bitcoin chain facts with provider attribution.",
        "capture_mode": capture_mode,
        "retrieved_at_utc": retrieved_at,
        "fixed_heights": [PRE_HEIGHT, HALVING_HEIGHT],
        "selection_rule": "the first 25 transactions by block index from each of two adjacent blocks, selected by the predeclared subsidy-halving height",
        "page_start_index": PAGE_START,
        "page_size_limit": PAGE_SIZE,
        "amount_unit": "satoshi",
        "subsidy_rule": "50 BTC right-shifted by floor(block height / 210000), in satoshis",
        "fee_recalculation": "for each non-coinbase transaction, sum input prevout values and subtract output values, then compare to the API fee field",
        "limitations": [
            "Each page covers only transaction indices 0 through 24 and is not a full-block fee sample.",
            "No inference about full-block fee totals, miner revenue trends, wallet identities, or causal effects is supported by two adjacent blocks.",
            "Coinbase payout minus nominal subsidy is a claimed amount above subsidy and is not labeled as total block fees.",
        ],
        "responses": response_hashes,
        "normalized_file": normalized_path.name,
        "normalized_sha256": sha256(normalized_bytes),
        "normalized_bytes": len(normalized_bytes),
    }
    if source_manifest_sha256 is not None:
        manifest["rebuild_source_manifest_sha256"] = source_manifest_sha256
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest_path = output / "bitcoin-halving.manifest.json"
    manifest_path.write_bytes(manifest_bytes)

    summary = []
    for item in page_records:
        txs = item["transactions"]
        noncoinbase = [tx for tx in txs if not tx["is_coinbase"]]
        coinbase = next(tx for tx in txs if tx["is_coinbase"])
        summary.append(
            {
                "height": item["block"]["height"],
                "timestamp": item["block"]["timestamp"],
                "block_transaction_count": item["block"]["tx_count"],
                "page_transaction_count": len(txs),
                "sample_noncoinbase_count": len(noncoinbase),
                "sample_noncoinbase_fee_sats": sum(int(tx["fee_sats"]) for tx in noncoinbase),
                "coinbase_payout_sats": coinbase["output_total_sats"],
                "nominal_subsidy_sats": coinbase["nominal_subsidy_sats"],
                "coinbase_payout_minus_subsidy_sats": coinbase["coinbase_payout_minus_subsidy_sats"],
            }
        )
    print(
        json.dumps(
            {
                "output_dir": str(output),
                "manifest": manifest_path.name,
                "manifest_sha256": sha256(manifest_bytes),
                "source_responses": len(response_hashes),
                "capture_mode": capture_mode,
                "summary": summary,
            },
            sort_keys=True,
        )
    )
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"capture failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
