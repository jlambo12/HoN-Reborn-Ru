#!/usr/bin/env python3
"""Create native game-HUD overrides for HoN Plus Live."""

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
        game_hd = zf.read("ui/game_hd.interface").decode("utf-8-sig")
    game_hd = replace_once(
        game_hd,
        '<lua file="/ui/scripts/game/damagebar.lua" />',
        '<lua file="/ui/scripts/game/damagebar.lua" />\n\t<lua file="/ui/scripts/game/honplus_live_data.lua" />\n\t<lua file="/ui/scripts/game/honplus_live.lua" />',
        "HoN Plus Lua insertion",
    )
    game_hd = replace_once(
        game_hd,
        '\t\t\tIGVanity_Shop:Init()',
        '\t\t\tIGVanity_Shop:Init()\n\t\t\tHoNPlusLive:Init()',
        "HoN Plus init insertion",
    )
    game_hd = replace_once(
        game_hd,
        '\t<!-- Vanity Shop -->',
        '\t<!-- HoN Plus Live -->\n\t<include file="/ui/hd_ui/sections/honplus_live.package" />\n\n\t<!-- Vanity Shop -->',
        "HoN Plus package insertion",
    )
    target_game = extended / "ui" / "game_hd.interface"
    target_game.parent.mkdir(parents=True, exist_ok=True)
    target_game.write_text(game_hd, encoding="utf-8", newline="")

    copied = 0
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        destination = extended / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copied += 1
    print(f"Prepared HoN Plus native HUD: game_hd.interface + {copied} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
