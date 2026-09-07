"""Create separate model-run freezes over unchanged challenge source and scorer bytes."""
import argparse
import hashlib
import json
from pathlib import Path

from native_run import frozen_inputs
from select_slots import _repo_file, challenge_dataset_context, manifest_content_hash

ROOT = Path(__file__).resolve().parents[1]
# These operational files may differ between the preserved pilot and final runtime.
RUNTIME_TRANSFER_INPUTS = {
    "config/runtime.json", "scripts/fix_native_version.py",
    "scripts/native_trial.py", "scripts/check_install.py",
}


def source_manifest(original, runtime, root):
    """Verify original cases and bind a separately frozen current runtime."""
    challenge_dataset_context(original["manifest_id"], root)
    manifest = dict(original)
    hashes = dict(original["hashes"])
    changed = {}
    for name, expected in hashes.items():
        actual = hashlib.sha256(_repo_file(root, name).read_bytes()).hexdigest()
        if actual == expected:
            continue
        if (name not in RUNTIME_TRANSFER_INPUTS
                or runtime["hashes"].get(name) != actual):
            raise ValueError("freeze_hash_mismatch")
        changed[name] = {"original": expected, "current": actual}
        hashes[name] = actual
    manifest["hashes"] = hashes
    if changed:
        manifest["runtime_manifest_id"] = runtime["manifest_id"]
        manifest["runtime_changes"] = changed
        if "settings" in runtime:
            manifest["settings"] = dict(runtime["settings"])
    return manifest


def create(model_file, root=ROOT):
    root = Path(root)
    relative = Path(model_file).absolute().relative_to(root.absolute()).as_posix()
    model_file = _repo_file(root, relative)
    profiles = json.loads(model_file.read_text())
    outputs = []
    development_id = None
    manifests = root / "datasets/challenge-v1/manifests"
    runtime_path = manifests / "evaluation.json"
    if not runtime_path.is_file():
        runtime_path = manifests / "development.json"
    if not runtime_path.is_file():
        raise ValueError("development_freeze_missing")
    runtime_original = json.loads(runtime_path.read_text())
    runtime = frozen_inputs(runtime_original["manifest_id"], root)
    for stage in ("development", "evaluation"):
        path = manifests / (stage + ".json")
        if not path.is_file():
            if stage == "evaluation":
                break
            raise ValueError("development_freeze_missing")
        original = json.loads(path.read_text())
        manifest = source_manifest(original, runtime, root)
        manifest["models"] = profiles
        manifest["base_manifest_id"] = original["manifest_id"]
        manifest["campaign_purpose"] = "Future model run on already published source cases, not a new held-out test set"
        manifest["hashes"][relative] = hashlib.sha256(model_file.read_bytes()).hexdigest()
        if stage == "evaluation":
            manifest["development_manifest_id"] = development_id
        manifest["budget"] = dict(manifest["budget"])
        count = 9 if stage == "development" else 27
        manifest["budget"]["reservation_usd"] = count * sum(v["reservation_usd_per_slot"] for v in profiles.values())
        manifest["content_hash"] = manifest_content_hash(manifest)
        manifest["manifest_id"] = f"challenge-v1-{stage}-" + manifest["content_hash"][:12]
        target = path.with_name(stage + "-" + manifest["content_hash"][:12] + ".json")
        data = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        created = not target.exists()
        if target.exists():
            if target.read_text() != data:
                raise ValueError("existing_campaign_manifest_changed")
        else:
            target.write_text(data)
        try:
            challenge_dataset_context(manifest["manifest_id"], root)
            frozen_inputs(manifest["manifest_id"], root)
        except Exception:
            if created:
                target.unlink()
            raise
        outputs.append(target)
        development_id = manifest["manifest_id"] if stage == "development" else development_id
        print(manifest["manifest_id"])
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("models", type=Path, help="Repository-local JSON with inexpensive and reference native model profiles")
    create(parser.parse_args().models)
