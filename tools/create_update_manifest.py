#!/usr/bin/env python3
"""Create the standalone manifest consumed by the autonomous launcher."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asset(path: Path, version: str = "") -> dict[str, object]:
    result: dict[str, object] = {
        "name": path.name,
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
    }
    if version:
        result["version"] = version
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--channel", choices=("stable", "beta"), required=True)
    parser.add_argument("--launcher-version", required=True)
    parser.add_argument("--translation", type=Path, required=True)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--updater", type=Path, required=True)
    parser.add_argument("--game-sha256", action="append", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()

    for path in (args.translation, args.launcher, args.updater):
        if not path.is_file():
            raise SystemExit(f"Required asset missing: {path}")
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    copied: dict[str, Path] = {}
    for source in (args.translation, args.launcher, args.updater):
        destination = output / source.name
        if source.resolve() != destination.resolve():
            shutil.copy2(source, destination)
        copied[source.name] = destination

    payload = {
        "schema_version": 1,
        "version": args.version,
        "channel": args.channel,
        "translation": asset(copied[args.translation.name]),
        "launcher": asset(copied[args.launcher.name], args.launcher_version),
        "updater": asset(copied[args.updater.name], args.launcher_version),
        "compatible_game_hashes": sorted({value.lower() for value in args.game_sha256}),
        "release_notes_url": f"https://github.com/jlambo12/HoN-Reborn-Ru/releases/tag/v{args.version}",
    }
    path = output / "update-manifest.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
