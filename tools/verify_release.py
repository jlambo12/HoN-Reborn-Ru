#!/usr/bin/env python3
"""Verify a distributable HoN Reborn RU overlay and its manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_MEMBERS = {
    "core_ru.resources",
    "juvio_options.json",
    "preact/dist/index.html",
    "preact/dist/index.js",
    "stringtables/entities_ru.str",
    "stringtables/interface_ru.str",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.1.0")
    args = parser.parse_args()

    asset_dir = ROOT / "release-assets" / args.version
    archive_path = asset_dir / "resources0.jz"
    manifest_path = asset_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    errors: list[str] = []
    actual_sha = sha256(archive_path)
    actual_size = archive_path.stat().st_size
    if manifest.get("version") != args.version:
        errors.append("manifest version mismatch")
    if manifest.get("sha256") != actual_sha:
        errors.append("SHA-256 mismatch")
    if manifest.get("size_bytes") != actual_size:
        errors.append("size mismatch")

    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            errors.append("duplicate archive member")
        if manifest.get("members") != len(names):
            errors.append("member count mismatch")
        missing = sorted(REQUIRED_MEMBERS.difference(names))
        if missing:
            errors.append(f"required members missing: {', '.join(missing)}")
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name:
                errors.append(f"unsafe archive member: {name}")
        corrupt = archive.testzip()
        if corrupt:
            errors.append(f"CRC failure: {corrupt}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: HoN Reborn RU v{args.version}")
    print(f"SHA-256: {actual_sha}")
    print(f"Members: {manifest['members']}; size: {actual_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

