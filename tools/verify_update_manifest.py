#!/usr/bin/env python3
"""Verify launcher update assets without trusting filenames or metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    root = args.directory.resolve()
    manifest_path = root / "update-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("unsupported schema")
    if manifest.get("channel") not in {"stable", "beta"}:
        errors.append("invalid channel")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", str(manifest.get("version", ""))):
        errors.append("invalid version")
    hashes = manifest.get("compatible_game_hashes", [])
    if not hashes or any(not re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes):
        errors.append("invalid compatible game hashes")
    for section in ("translation", "launcher", "updater"):
        item = manifest.get(section, {})
        name = item.get("name", "")
        if Path(name).name != name or not name:
            errors.append(f"unsafe {section} asset name")
            continue
        path = root / name
        if not path.is_file():
            errors.append(f"missing {section} asset")
            continue
        if path.stat().st_size != item.get("size_bytes"):
            errors.append(f"{section} size mismatch")
        if sha256(path) != item.get("sha256"):
            errors.append(f"{section} SHA-256 mismatch")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: update manifest {manifest['version']} ({manifest['channel']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
