#!/usr/bin/env python3
"""Create the native vanity-package override for HoN Plus Live."""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{label} invariant changed: expected one marker, found {text.count(old)}")
    return text.replace(old, new)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    archive = args.archive.resolve()
    extended = (root / "src" / "extended_ru").resolve()
    source = (root / "src" / "honplus_native").resolve()
    if extended != (root / "src" / "extended_ru").resolve():
        raise SystemExit("Unsafe extended root")

    with zipfile.ZipFile(archive) as zf:
        vanity = zf.read("ui/hd_ui/sections/ig_vanity_shop.package").decode("utf-8-sig")
    data_files = sorted((source / "ui" / "scripts" / "game").glob("honplus_live_data*.lua"))
    if not data_files or data_files[0].name != "honplus_live_data.lua":
        raise SystemExit("HoN Plus generated benchmark files are missing")
    lua_includes = "\n".join(
        f'\t<lua file="/ui/scripts/game/{path.name}" />' for path in data_files
    )
    live_package = (source / "ui" / "hd_ui" / "sections" / "honplus_live.package").read_text(encoding="utf-8")
    live_body = live_package.removeprefix('<?xml version="1.0" encoding="UTF-8"?>').strip()
    if not live_body.startswith("<package>") or not live_body.endswith("</package>"):
        raise SystemExit("HoN Plus package wrapper invariant changed")
    live_body = live_body[len("<package>"):-len("</package>")].strip()
    vanity = replace_once(
        vanity,
        "<package>",
        "<package>\n\n\t<!-- HoN Plus Live Lua -->\n" + lua_includes + '\n\t<lua file="/ui/scripts/game/honplus_live.lua" />',
        "Vanity package Lua insertion",
    )
    vanity = replace_once(
        vanity,
        "</package>",
        "\n\t<!-- HoN Plus Live panel -->\n" + live_body + "\n\n</package>",
        "Vanity package panel insertion",
    )
    target_vanity = extended / "ui" / "hd_ui" / "sections" / "ig_vanity_shop.package"
    target_vanity.parent.mkdir(parents=True, exist_ok=True)
    target_vanity.write_text(vanity, encoding="utf-8", newline="")

    stale_game = extended / "ui" / "game_hd.interface"
    if stale_game.is_file() and "honplus_live" in stale_game.read_text(encoding="utf-8"):
        stale_game.unlink()

    copied = 0
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        destination = extended / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copied += 1
    print(f"Prepared HoN Plus native HUD in vanity package + {copied} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
