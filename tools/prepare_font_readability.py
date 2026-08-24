#!/usr/bin/env python3
"""Prepare reviewable, RU-only font/readability overrides.

Inputs are read-only. Output is isolated under src/font_readability_ru/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


ACTIVE_TEXT_STYLES = {
    "color-white",
    "section_title",
    "h1", "h2", "h3", "h4", "h5",
    "text_base",
    "sysbar_menu_label",
    "tutorial_h1", "tutorial_h2",
    "tip_textSmaller", "tip_textSmall", "tip_textMedium", "tip_textBig", "tip_textBigger",
}
CYRILLIC_RANGE = "U+0400-052F, U+2DE0-2DFF, U+A640-A69F"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--game-archive", type=Path, required=True)
    parser.add_argument("--phase2a-build", type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    game = args.game_archive.resolve()
    phase2a = (args.phase2a_build or root / "build" / "phase2a" / "resources0.jz").resolve()
    output = root / "src" / "font_readability_ru"

    with zipfile.ZipFile(game) as zf:
        core = zf.read("core_en.resources").decode("utf-8-sig")
        styles = zf.read("ui/hd_ui/styles.package").decode("utf-8-sig")

    # The HoN TTFs contain TrueType hint programs and complete Cyrillic glyphs.
    # Re-enable those programs without touching font size, scaling, gamma or outline.
    core, hint_changes = re.subn(r'\s+nohinting="true"', "", core)
    if hint_changes != 56:
        raise SystemExit(f"core fontmap invariant changed: expected 56 nohinting flags, got {hint_changes}")

    # Raise only primary/active native text from 90% to 95% white. Muted,
    # disabled, placeholder and gameplay semantic colors remain untouched.
    style_changes: list[str] = []

    def brighten(match: re.Match[str]) -> str:
        block = match.group(0)
        name_match = re.search(r'\bname="([^"]+)"', block)
        if not name_match or name_match.group(1) not in ACTIVE_TEXT_STYLES:
            return block
        updated, count = re.subn(r'\bcolor="\.9 \.9 \.9 1"', 'color=".95 .95 .95 1"', block)
        if count:
            style_changes.append(name_match.group(1))
        return updated

    styles = re.sub(r"<style\b.*?\s*/>", brighten, styles, flags=re.I | re.S)
    expected_styles = ACTIVE_TEXT_STYLES - {"color-white"}
    if set(style_changes) != ACTIVE_TEXT_STYLES:
        missing = sorted(ACTIVE_TEXT_STYLES - set(style_changes))
        extra = sorted(set(style_changes) - ACTIVE_TEXT_STYLES)
        raise SystemExit(f"style invariant changed; missing={missing}, extra={extra}")

    with zipfile.ZipFile(phase2a) as zf:
        css = zf.read("preact/dist/assets/index.css").decode("utf-8")
    marker = "/* HoN RU Cyrillic fallback: existing HoN fonts, no new typeface. */"
    if marker in css:
        raise SystemExit("Phase 2A CSS already contains font readability override")
    css_override = f"""

{marker}
@font-face{{font-family:Inter;src:url('/assets/fonts/hon_intl.ttf') format('truetype');font-weight:400 500;font-style:normal;unicode-range:{CYRILLIC_RANGE}}}
@font-face{{font-family:Inter;src:url('/assets/fonts/hon_bold_intl.ttf') format('truetype');font-weight:600 800;font-style:normal;unicode-range:{CYRILLIC_RANGE}}}
"""
    css += css_override

    generated = {
        "core_ru.resources": core.encode("utf-8"),
        "ui/hd_ui/styles.package": styles.encode("utf-8"),
        "preact/dist/assets/index.css": css.encode("utf-8"),
    }
    for relative, data in generated.items():
        write(output / Path(*relative.split("/")), data)

    manifest = {
        "source_game_archive": str(game),
        "source_phase2a_build": str(phase2a),
        "output_root": str(output),
        "changes": {
            "hinting_flags_removed": hint_changes,
            "brightened_active_styles": sorted(style_changes),
            "active_text_color_before": ".9 .9 .9 1 (#E6E6E6 rounded)",
            "active_text_color_after": ".95 .95 .95 1 (#F2F2F2 rounded)",
            "preact_inter_cyrillic_fallback": "existing HoN Regular/Bold glyphs",
            "cyrillic_unicode_range": CYRILLIC_RANGE,
        },
        "unchanged": [
            "font sizes and UI layout",
            "dynamic_fontsize/baseresolution/axis scaling",
            "gamma and outline thickness",
            "shadows, disabled/muted/placeholder colors",
            "orange/yellow/green/red gameplay markup",
            "all tutorial images and localization strings",
        ],
        "files": {relative: {"size_bytes": len(data), "sha256": sha256(data)} for relative, data in generated.items()},
    }
    manifest_path = root / "reports" / "font_readability_overrides.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["changes"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
