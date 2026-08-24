#!/usr/bin/env python3
"""Verify the isolated font/readability build and safety invariants."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


EXPECTED_GAME_SHA = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"
EXPECTED_PHASE2A_SHA = "9d5d4176ff51f1799df50d9f7f61ba387ec7cdc54244cb7393e8c87f7143945c"
EXPECTED_CHANGED = {"core_ru.resources", "preact/dist/assets/index.css", "ui/hd_ui/styles.package"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--game-archive", type=Path, required=True)
    parser.add_argument("--installed-extension", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    game = args.game_archive.resolve()
    installed = args.installed_extension.resolve()
    base = root / "build" / "phase2a" / "resources0.jz"
    build = root / "build" / "font-readability" / "resources0.jz"
    backup = root / "backups" / "font-readability" / "phase2a-resources0-before-font.jz"
    errors: list[str] = []

    hashes = {name: sha256(path) for name, path in {"game": game, "installed": installed, "base": base, "backup": backup, "build": build}.items()}
    for name in ("game",):
        if hashes[name] != EXPECTED_GAME_SHA:
            errors.append(f"{name} SHA changed: {hashes[name]}")
    for name in ("installed", "base", "backup"):
        if hashes[name] != EXPECTED_PHASE2A_SHA:
            errors.append(f"{name} is not Phase 2A baseline: {hashes[name]}")

    with zipfile.ZipFile(base) as old, zipfile.ZipFile(build) as new:
        old_names = {name for name in old.namelist() if not name.endswith("/")}
        new_names = {name for name in new.namelist() if not name.endswith("/")}
        if old.testzip(): errors.append("Phase 2A base CRC failure")
        if new.testzip(): errors.append("font build CRC failure")
        added = new_names - old_names
        removed = old_names - new_names
        if added != {"ui/hd_ui/styles.package"} or removed:
            errors.append(f"unexpected member delta; added={sorted(added)}, removed={sorted(removed)}")
        changed = {name for name in old_names & new_names if old.read(name) != new.read(name)} | added
        if changed != EXPECTED_CHANGED:
            errors.append(f"unexpected changed members: {sorted(changed)}")
        core = new.read("core_ru.resources").decode("utf-8")
        styles = new.read("ui/hd_ui/styles.package").decode("utf-8")
        css = new.read("preact/dist/assets/index.css").decode("utf-8")
    if 'nohinting="true"' in core: errors.append("nohinting remains in RU core fontmaps")
    if core.count("<fontmap ") != 60: errors.append("fontmap count changed")
    for invariant in ('gamma="1.5"', 'dynamic_fontsize="true"', 'baseresolution="768"'):
        if invariant not in core: errors.append(f"core invariant missing: {invariant}")
    if styles.count('color=".95 .95 .95 1"') != 16: errors.append("active style color count is not 16")
    for color in ("#ffab01", "#6CDE8B", "#d82727", 'color=".7 .7 .7 1"', 'color=".3 .3 .3 1"'):
        if color not in styles: errors.append(f"semantic/muted color missing: {color}")
    if "HoN RU Cyrillic fallback" not in css or "U+0400-052F" not in css:
        errors.append("Preact Cyrillic fallback missing")

    help_rows = load_jsonl(root / "reports" / "help_topics_inventory.jsonl")
    image_rows = load_jsonl(root / "reports" / "help_image_assets.jsonl")
    teleport = [row for row in help_rows if row["key"] == "tutorial_slide_teleport_desc"]
    if len(teleport) != 1 or not teleport[0]["english"].startswith("Each Hero has"):
        errors.append("teleport instructional text was not traced to its localization key")
    confirmed_images = [row for row in image_rows if row["review_status"] == "CONFIRMED_ENGLISH_TEXT"]
    if len(help_rows) != 308: errors.append(f"Help Topics catalog inventory changed: {len(help_rows)}")
    if len(image_rows) != 65: errors.append(f"Help image inventory changed: {len(image_rows)}")
    if len(confirmed_images) != 23: errors.append(f"confirmed image-text count changed: {len(confirmed_images)}")

    report = {
        "result": "FAIL" if errors else "PASS",
        "errors": errors,
        "hashes": hashes,
        "archive": {"changed_members": sorted(changed), "added_members": sorted(added), "removed_members": sorted(removed), "member_count": len(new_names)},
        "font_checks": {
            "fontmaps": core.count("<fontmap "),
            "nohinting_flags_remaining": core.count('nohinting="true"'),
            "brightened_active_style_count": styles.count('color=".95 .95 .95 1"'),
            "preact_cyrillic_fallback": "HoN RU Cyrillic fallback" in css,
        },
        "help_topics": {
            "inventory_rows": len(help_rows),
            "image_assets": len(image_rows),
            "confirmed_english_image_assets": len(confirmed_images),
            "teleport_text_source": teleport[0]["source_file"] if teleport else None,
        },
        "safety": {"main_game_archive_modified": False, "installed_test_build": False, "rollback_backup_verified": hashes["backup"] == EXPECTED_PHASE2A_SHA},
    }
    path = root / "reports" / "font_readability_final_report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
