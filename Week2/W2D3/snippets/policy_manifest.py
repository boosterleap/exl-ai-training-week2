"""Index-time integrity manifest for the policy documents rag_index.py chunks.

Computes a SHA-256 checksum per file under data/insurance/policies/ and
data/logistics/policies/ and saves it to a manifest keyed by source_file
(the same field name rag_index.py's chunks carry), alongside the timestamp
the manifest was built. A later "check" recomputes checksums against the
live files and reports drift: changed, added, or removed files -- i.e.
whether the LanceDB index is still faithful to what's on disk.

Run it:
    uv run python W2D3/snippets/policy_manifest.py build
    uv run python W2D3/snippets/policy_manifest.py check
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


REPO_ROOT = discover_repo_root()
POLICIES_DIRS = [REPO_ROOT / "data" / "insurance" / "policies", REPO_ROOT / "data" / "logistics" / "policies"]
MANIFEST_PATH = REPO_ROOT / "W2D3" / "outputs" / "policy_manifest.json"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_checksums() -> dict[str, str]:
    checksums: dict[str, str] = {}
    for directory in POLICIES_DIRS:
        for md_file in sorted(directory.glob("*.md")):
            checksums[md_file.name] = sha256_of(md_file)
    return checksums


def build_manifest() -> dict[str, object]:
    manifest = {
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "checksums": current_checksums(),
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def check_drift() -> dict[str, list[str]]:
    """Compare the live files against the saved manifest -- returns changed/added/removed."""
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"No manifest at {MANIFEST_PATH}. Run 'build' first.")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    recorded: dict[str, str] = manifest["checksums"]
    live = current_checksums()

    changed = sorted(name for name in recorded.keys() & live.keys() if recorded[name] != live[name])
    added = sorted(live.keys() - recorded.keys())
    removed = sorted(recorded.keys() - live.keys())
    return {"changed": changed, "added": added, "removed": removed}


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "check"

    if command == "build":
        manifest = build_manifest()
        print(f"Manifest written to {MANIFEST_PATH}")
        print(f"indexed_at: {manifest['indexed_at']}")
        print(f"{len(manifest['checksums'])} files recorded.")
        return

    if command == "check":
        drift = check_drift()
        if not any(drift.values()):
            print("No drift: every file matches the manifest.")
            return
        if drift["changed"]:
            print(f"CHANGED ({len(drift['changed'])}) -- reindex needed:")
            for name in drift["changed"]:
                print(f"  {name}")
        if drift["added"]:
            print(f"ADDED ({len(drift['added'])}) -- not yet in the index:")
            for name in drift["added"]:
                print(f"  {name}")
        if drift["removed"]:
            print(f"REMOVED ({len(drift['removed'])}) -- stale chunks still in the index:")
            for name in drift["removed"]:
                print(f"  {name}")
        return

    raise SystemExit(f"Unknown command {command!r}. Use 'build' or 'check'.")


if __name__ == "__main__":
    main()
