#!/usr/bin/env python3
"""Write or verify the repository SHA-256 inventory."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "CHECKSUMS.sha256"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def versioned_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path == INVENTORY:
            continue
        if ".git" in path.parts or ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        files.append(path)
    return sorted(files, key=lambda item: str(item.relative_to(ROOT)))


def write_inventory() -> None:
    lines = [f"{sha256(path)}  {path.relative_to(ROOT)}" for path in versioned_files()]
    INVENTORY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {INVENTORY} with {len(lines)} entries")


def verify_inventory() -> None:
    expected = {}
    for line in INVENTORY.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        expected[relative] = digest
    actual_paths = {str(path.relative_to(ROOT)): path for path in versioned_files()}
    missing = sorted(set(expected).difference(actual_paths))
    extra = sorted(set(actual_paths).difference(expected))
    changed = sorted(relative for relative, path in actual_paths.items() if relative in expected and sha256(path) != expected[relative])
    if missing or extra or changed:
        for label, values in [("missing", missing), ("extra", extra), ("changed", changed)]:
            for value in values:
                print(f"FAIL {label}: {value}")
        raise SystemExit("checksum verification failed")
    print(f"checksum verification passed for {len(expected)} files")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="write CHECKSUMS.sha256")
    group.add_argument("--verify", action="store_true", help="verify CHECKSUMS.sha256")
    args = parser.parse_args()
    if args.write:
        write_inventory()
    else:
        verify_inventory()


if __name__ == "__main__":
    main()
