#!/usr/bin/env python3
"""Read-only font/rendering and Learn -> Help Topics inventory.

The game archive is opened only for reading. Generated evidence is written under
reports/ and optional image extracts under build/font-audit/help-images/.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET


TEXT_SUFFIXES = {".interface", ".package", ".resources", ".lua", ".css", ".tsx", ".ts", ".js", ".xml"}
FONT_SUFFIXES = {".ttf", ".otf", ".woff", ".woff2", ".fnt"}
IMAGE_SUFFIXES = {".png", ".tga", ".jpg", ".jpeg", ".webp", ".dds"}
HELP_FILE_RE = re.compile(r"(?:tutorial|help|learn)", re.I)
IMAGE_REF_RE = re.compile(r"[\"'](/?ui/fe3/npe/[^\"']+?\.(?:png|tga|jpe?g|webp|dds))[\"']", re.I)
KEY_TOKEN_RE = re.compile(r"[\"']([A-Za-z][A-Za-z0-9_]*)[\"']")
STYLE_ATTR_RE = re.compile(
    r"\b(font|fontface|fontsize|color|textcolor|alpha|textalpha|shadow|textshadow|outline|glow|scale|uiscale|dpi|filter|mipmap)\s*=\s*([\"'])(.*?)\2",
    re.I,
)
CSS_DECL_RE = re.compile(
    r"\b(font(?:-family|-size|-weight|-style|-stretch)?|color|opacity|text-shadow|filter|transform)\s*:\s*([^;}]+)",
    re.I,
)
RU_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
LATIN_SAMPLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
CONFIRMED_IMAGE_TEXT = {
    "ui/fe3/npe/auto-level.png": "Search, Focus, Auto, guide/item section labels",
    "ui/fe3/npe/bans.png": "full English lobby/matchmaking screenshot",
    "ui/fe3/npe/bot-center-courier.png": "Deliverable",
    "ui/fe3/npe/cosmetics.png": "Cosmetics, Courier, Available to Buy or Rent, product/action labels",
    "ui/fe3/npe/courier.png": "PlayerName, Away",
    "ui/fe3/npe/custom-games.png": "full English custom-game screenshot",
    "ui/fe3/npe/custom-lobby.png": "full English custom-lobby screenshot",
    "ui/fe3/npe/emoteshop.png": "Emotes, category/product/action labels",
    "ui/fe3/npe/emoteuse.png": "Close, Breaking News",
    "ui/fe3/npe/game-modes.png": "full English matchmaking screenshot",
    "ui/fe3/npe/gold-shop.png": "Search, Focus, guide/item section labels",
    "ui/fe3/npe/honor-profile.png": "full English profile/honor screenshot",
    "ui/fe3/npe/honor.png": "full English Honor System screenshot",
    "ui/fe3/npe/invite-teammates.png": "full English matchmaking screenshot",
    "ui/fe3/npe/ladder.png": "full English ladder screenshot",
    "ui/fe3/npe/learn.png": "full English Learn screen screenshot",
    "ui/fe3/npe/limited-hero-pool.png": "Agility, Intelligence, Strength",
    "ui/fe3/npe/matchmaking-tuning.png": "full English matchmaking screenshot",
    "ui/fe3/npe/mini-map-fort.png": "Fortification of Sol tooltip and Defense Tower panel",
    "ui/fe3/npe/plinko.png": "full English Plinko screenshot",
    "ui/fe3/npe/quick-buy.png": "Quick Buy, item names, Search/Focus and instructions",
    "ui/fe3/npe/role-priorities.png": "full English matchmaking screenshot",
    "ui/fe3/npe/teleport.png": "PlayerName, Teleportation Stone",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


def tt_name(font, name_id: int) -> str:
    for record in font["name"].names:
        if record.nameID == name_id:
            try:
                return record.toUnicode()
            except Exception:
                continue
    return ""


def font_record(name: str, data: bytes, fonttools_path: Path) -> dict:
    sys.path.insert(0, str(fonttools_path))
    try:
        from fontTools.ttLib import TTFont

        font = TTFont(io.BytesIO(data), lazy=False)
        cmap: dict[int, str] = {}
        for table in font["cmap"].tables:
            if table.isUnicode():
                cmap.update(table.cmap)
        widths = font["hmtx"].metrics
        latin_width = [widths[cmap[ord(char)]][0] for char in LATIN_SAMPLE if ord(char) in cmap and cmap[ord(char)] in widths]
        ru_width = [widths[cmap[ord(char)]][0] for char in RU_ALPHABET if ord(char) in cmap and cmap[ord(char)] in widths]
        os2 = font.get("OS/2")
        return {
            "path": name,
            "size_bytes": len(data),
            "sha256": sha256_bytes(data),
            "family": tt_name(font, 1),
            "subfamily": tt_name(font, 2),
            "version": tt_name(font, 5),
            "units_per_em": font["head"].unitsPerEm,
            "glyphs": len(font.getGlyphOrder()),
            "hint_tables": {tag: tag in font for tag in ("cvt ", "fpgm", "prep", "gasp")},
            "cyrillic_codepoints": sum(0x0400 <= cp <= 0x052F for cp in cmap),
            "missing_russian": "".join(char for char in RU_ALPHABET if ord(char) not in cmap),
            "avg_latin_advance": round(sum(latin_width) / len(latin_width), 2) if latin_width else None,
            "avg_russian_advance": round(sum(ru_width) / len(ru_width), 2) if ru_width else None,
            "x_height": getattr(os2, "sxHeight", None) if os2 else None,
            "cap_height": getattr(os2, "sCapHeight", None) if os2 else None,
        }
    except Exception as exc:
        return {"path": name, "size_bytes": len(data), "sha256": sha256_bytes(data), "error": str(exc)}


def image_dimensions(data: bytes, suffix: str) -> tuple[int | None, int | None]:
    if suffix == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    try:
        from PIL import Image

        with Image.open(io.BytesIO(data)) as image:
            return image.size
    except Exception:
        return None, None


def normalize_member(path: str) -> str:
    return str(PurePosixPath(path.lstrip("/"))).replace("\\", "/")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--extract-help-images", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve()
    archive = args.archive.resolve()
    reports = root / "reports"
    extract_root = root / "build" / "font-audit" / "help-images"
    fonttools_path = root / "build" / "font-audit" / "pydeps"
    catalog = load_jsonl(root / "catalog" / "strings.jsonl")
    catalog_by_key: dict[str, list[dict]] = defaultdict(list)
    for row in catalog:
        catalog_by_key[row["key"]].append(row)

    with zipfile.ZipFile(archive) as zf:
        members = {normalize_member(info.filename): info for info in zf.infolist() if not info.is_dir()}
        text_members: dict[str, str] = {}
        fonts = []
        for name, info in members.items():
            suffix = PurePosixPath(name).suffix.lower()
            if suffix in TEXT_SUFFIXES and info.file_size <= 8 * 1024 * 1024:
                text_members[name] = decode_text(zf.read(info))
            if suffix in FONT_SUFFIXES:
                fonts.append(font_record(name, zf.read(info), fonttools_path))

        core_text = text_members.get("core_en.resources", "")
        fontmaps = []
        try:
            tree = ET.fromstring(core_text)
            for face in tree.findall("fontface"):
                for item in face.findall("fontmap"):
                    fontmaps.append({"source": "core_en.resources", "fontface": face.attrib.get("file"), **item.attrib})
        except ET.ParseError as exc:
            fontmaps.append({"source": "core_en.resources", "parse_error": str(exc)})

        style_counts: Counter[tuple[str, str]] = Counter()
        style_sources: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
        hotspots: Counter[str] = Counter()
        for name, text_value in text_members.items():
            matches = [(m.group(1).lower(), m.group(3).strip()) for m in STYLE_ATTR_RE.finditer(text_value)]
            matches += [(m.group(1).lower(), m.group(2).strip()) for m in CSS_DECL_RE.finditer(text_value)]
            if matches:
                hotspots[name] += len(matches)
            for prop, value in matches:
                style_counts[(prop, value)] += 1
                style_sources[(prop, value)][name] += 1

        styles = [
            {
                "property": prop,
                "value": value,
                "occurrences": count,
                "top_sources": [{"path": path, "count": n} for path, n in style_sources[(prop, value)].most_common(8)],
            }
            for (prop, value), count in style_counts.most_common()
        ]

        help_sources = {
            name: text_value for name, text_value in text_members.items()
            if HELP_FILE_RE.search(name)
            and (name.startswith("ui/") or name.startswith("stringtables/"))
        }
        referenced_keys: dict[str, set[str]] = defaultdict(set)
        referenced_images: dict[str, set[str]] = defaultdict(set)
        for source, text_value in help_sources.items():
            for match in KEY_TOKEN_RE.finditer(text_value):
                key = match.group(1)
                if key in catalog_by_key:
                    referenced_keys[key].add(source)
            for match in IMAGE_REF_RE.finditer(text_value):
                referenced_images[normalize_member(match.group(1))].add(source)

        # Catalog prefixes include strings assembled indirectly by Tutorial Lua.
        help_key_re = re.compile(r"^(?:tutorial_|help_|learn_|npe_)", re.I)
        inventory_rows = []
        for row in catalog:
            if row["key"] in referenced_keys or help_key_re.search(row["key"]) or row.get("category") == "help_tutorial":
                inventory_rows.append({
                    "id": row["id"],
                    "key": row["key"],
                    "kind": "UI_LOCALIZATION_STRING",
                    "english": row["english"],
                    "russian": row.get("russian", ""),
                    "status": row["status"],
                    "category": row["category"],
                    "source_file": row["source_file"],
                    "source_line": row["source_line"],
                    "runtime_sources": sorted(referenced_keys.get(row["key"], set())),
                })
        inventory_rows.sort(key=lambda row: (row["key"].lower(), row["id"]))

        image_rows = []
        all_npe_assets = sorted(name for name in members if name.lower().startswith("ui/fe3/npe/") and PurePosixPath(name).suffix.lower() in IMAGE_SUFFIXES)
        for name in all_npe_assets:
            data = zf.read(members[name])
            width, height = image_dimensions(data, PurePosixPath(name).suffix.lower())
            sources = sorted(referenced_images.get(name, set()))
            confirmed_text = CONFIRMED_IMAGE_TEXT.get(name, "")
            image_rows.append({
                "id": f"image:{name}",
                "kind": "IMAGE_TEXT",
                "asset": name,
                "size_bytes": len(data),
                "width": width,
                "height": height,
                "sha256": sha256_bytes(data),
                "referenced": bool(sources),
                "runtime_sources": sources,
                "review_status": "CONFIRMED_ENGLISH_TEXT" if confirmed_text else "NO_ENGLISH_TEXT_OBSERVED",
                "english_text": confirmed_text,
                "load_method": "native texture path from tutorial package/Lua",
            })
            if args.extract_help_images and sources:
                output = extract_root / Path(*PurePosixPath(name).parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(data)

    font_report = {
        "archive": str(archive),
        "archive_sha256": sha256_bytes(archive.read_bytes()),
        "fonts": sorted(fonts, key=lambda item: item["path"]),
        "fontmaps": fontmaps,
        "conclusions": {
            "native_bitmap_ui_atlas_found": any(PurePosixPath(item["path"]).suffix.lower() == ".fnt" for item in fonts),
            "native_hon_hinting_disabled": [item.get("name") for item in fontmaps if item.get("nohinting") == "true"],
            "fontmaps_claiming_cyrillic": [item.get("name") for item in fontmaps if "cyrillic" in item.get("language", "")],
        },
    }
    style_report = {
        "archive": str(archive),
        "scanned_text_files": len(text_members),
        "matched_declarations": sum(style_counts.values()),
        "hotspots": [{"path": path, "matches": count} for path, count in hotspots.most_common(100)],
        "styles": styles,
    }
    help_summary = {
        "catalog_rows": len(inventory_rows),
        "translated_rows": sum(bool(row["russian"]) for row in inventory_rows),
        "untranslated_rows": sum(not row["russian"] for row in inventory_rows),
        "runtime_referenced_rows": sum(bool(row["runtime_sources"]) for row in inventory_rows),
        "npe_image_assets": len(image_rows),
        "referenced_image_assets": sum(row["referenced"] for row in image_rows),
        "confirmed_english_image_assets": sum(row["review_status"] == "CONFIRMED_ENGLISH_TEXT" for row in image_rows),
        "help_source_files": sorted(help_sources),
        "note": "IMAGE_TEXT rows are an audit registry only; no image was modified.",
    }
    write_json(reports / "font_resource_inventory.json", font_report)
    write_json(reports / "font_style_inventory.json", style_report)
    write_jsonl(reports / "help_topics_inventory.jsonl", inventory_rows)
    write_jsonl(reports / "help_image_assets.jsonl", image_rows)
    write_json(reports / "help_topics_summary.json", help_summary)
    print(json.dumps({"font_files": len(fonts), "fontmaps": len(fontmaps), **help_summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
