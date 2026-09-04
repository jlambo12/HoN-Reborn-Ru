#!/usr/bin/env python3
"""Build a deterministic thin release overlay from a verified HoN Plus build."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


ALIASED_DOMAINS = ("bot_messages", "client_messages", "entities", "game_messages", "interface")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_ZSTANDARD
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--previous-version", required=True)
    parser.add_argument("--build", type=Path, required=True)
    args = parser.parse_args()
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required for ZIP Zstandard output")

    root = args.project_root.resolve()
    build = args.build.resolve()
    previous = root / "release-assets" / args.previous_version / "resources0.jz"
    output_dir = root / "release-assets" / args.version
    output = output_dir / "resources0.jz"
    honplus_root = root / "src" / "honplus_native"
    if not build.is_file() or not previous.is_file():
        raise SystemExit("Verified build or previous release archive is missing")

    # Publication must consume the validated cumulative thin overlay, never
    # silently combine an old UI screen with a newer game's Lua dependencies.
    report_path = root / "translation" / "reports" / "human_current_rebase.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("result") != "PASS" or report["output"]["sha256"] != sha256(build):
        raise SystemExit("Use the validated build/human-ru-current/resources0.jz")

    with zipfile.ZipFile(previous) as old, zipfile.ZipFile(build) as candidate:
        if old.testzip() is not None or candidate.testzip() is not None:
            raise SystemExit("Input archive CRC check failed")
        old_names = {name for name in old.namelist() if not name.endswith("/")}
        candidate_names = {name for name in candidate.namelist() if not name.endswith("/")}
        members: dict[str, bytes] = {}
        if missing := sorted(old_names - candidate_names):
            raise SystemExit(f"Cumulative overlay lost previous members: {missing}")
        for name in sorted(candidate_names):
            members[name] = candidate.read(name)

        honplus_names = {
            path.relative_to(honplus_root).as_posix()
            for path in honplus_root.rglob("*") if path.is_file()
        }
        honplus_names.add("ui/hd_ui/sections/ig_vanity_shop.package")
        missing = sorted(honplus_names - candidate_names)
        if missing:
            raise SystemExit(f"HoN Plus build members missing: {missing}")
        for name in sorted(honplus_names):
            members[name] = candidate.read(name)

        for domain in ALIASED_DOMAINS:
            ru_name = f"stringtables/{domain}_ru.str"
            members[f"stringtables/{domain}_en.str"] = members[ru_name]

    required = {
        "juvio_options.json", "preact/dist/index.js", "preact-remote/dist/index.js",
        "ui/hd_ui/sections/honplus_live.package",
        "ui/hd_ui/sections/ig_vanity_shop.package",
        "ui/scripts/game/honplus_live.lua",
    }
    if missing := sorted(required - members.keys()):
        raise SystemExit(f"Required release members missing: {missing}")

    output_dir.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.building")
    with zipfile.ZipFile(temporary, "w", allowZip64=True) as archive:
        for name, data in sorted(members.items()):
            write_member(archive, name, data)
    temporary.replace(output)
    with zipfile.ZipFile(output) as archive:
        corrupt = archive.testzip()
        count = len(archive.infolist())
    if corrupt:
        raise SystemExit(f"Output CRC failure: {corrupt}")

    manifest = {
        "schema_version": 1,
        "version": args.version,
        "file": output.name,
        "sha256": sha256(output),
        "size_bytes": output.stat().st_size,
        "members": count,
        "crc": "PASS",
        "automated_tests": "PASS",
        "runtime_verified": False,
        "runtime_status": "Automated archive and regression checks passed; in-game verification pending user feedback. No local installation performed.",
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
