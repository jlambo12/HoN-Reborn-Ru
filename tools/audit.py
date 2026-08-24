#!/usr/bin/env python3
"""Read-only inventory and localization catalog builder for HoN Reborn.

Python 3.14+ is required because resources0.jz contains ZIP method 93
(Zstandard) members. The installed archive is never opened for writing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable, Iterator


KNOWN_SHA256 = "58fbed1ed7e5507a72c4ab718b757187395e59e75ca5d9a47d3a89e2fa398364"
STATUS_VALUES = {"TRANSLATE", "KEEP_EN", "REVIEW", "DYNAMIC", "IMAGE_TEXT", "DEPRECATED"}

TEXT_EXTENSIONS = {
    ".ability", ".announcer", ".cfg", ".client", ".css", ".effect",
    ".entity", ".game", ".gamemechanics", ".gadget", ".hero", ".html",
    ".interface", ".item", ".js", ".json", ".lua", ".material", ".md",
    ".mjs", ".package", ".projectile", ".resources", ".state", ".str",
    ".ts", ".tsx", ".txt", ".xml",
}

RELEVANT_TERMS = (
    "stringtable", "locale", "language", "region", "font", "help", "tutorial",
    "hero", "abilit", "item", "boss", "matchmaking", "profile", "ladder",
    "leaderboard", "store", "replay", "notification", "announcer", "preact",
    "motd", "news", "patch", "jade", "vanity", "emote",
)

EXTRACT_EXACT = {
    "core_en.resources", "core_th.resources", "game_options.json",
    "juvio_options.json", "ui/scripts/fe3/regions.lua", "html/auto-load.js",
    "preact/auto-load.js", "preact/index.html", "preact/dist/index.html",
    "preact-remote/index.html", "ui/confirmations.interface",
    "ui/fe3/sections/game_lobby.package", "ui/fe3/sections/ladder.package",
    "ui/fe3/sections/match_stats.package", "ui/fe3/sections/motd.package",
    "ui/fe3/sections/patch_notes.package", "ui/fe3/sections/profilev2.package",
    "preact/dist/hon-content/media/img/patch-0-10-0/classic-shop.webp",
    "preact/dist/hon-content/media/img/patch-0-10-0/cosmetics-store.webp",
    "preact/dist/hon-content/media/img/patch-0-10-0/keybindings-toggle.webp",
    "preact/dist/hon-content/media/img/patch-0-10-0/npe-1.webp",
    "preact/dist/hon-content/media/img/patch-0-10-0/npe-2.webp",
}

CATALOG_FIELDS = [
    "id", "key", "english", "thai", "source_file", "source_line", "namespace",
    "category", "context", "status", "runtime_role", "thai_signal",
    "protected_reason", "protected_terms", "locked_spans", "russian", "notes", "english_hash",
    "classification_version", "classification_source",
]

PREACT_FIELDS = [
    "literal", "source_file", "source_line", "kind", "layer", "status", "notes",
]


@dataclass(frozen=True)
class StringEntry:
    key: str
    value: str
    line: int


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid existing JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def merge_english_changed(row: dict, previous: dict) -> None:
    """Merge a changed upstream value without reviewing untranslated work."""
    was_protected = previous.get("status") == "KEEP_EN" and previous.get("classification_source") == "HUMAN"
    prior_russian = previous.get("russian", "")
    if row["status"] == "KEEP_EN" or was_protected:
        row["status"] = "KEEP_EN"
        row["russian"] = row["english"]
        if was_protected and not row.get("protected_reason"):
            row["protected_reason"] = previous.get("protected_reason", "Previously approved protected content")
    elif prior_russian:
        row["status"] = "REVIEW"
        row["russian"] = prior_russian
    else:
        row["russian"] = ""
    prior_notes = previous.get("notes", "").strip()
    note = "English changed; translation review required" if prior_russian else "English changed before translation; current classification retained"
    row["notes"] = "; ".join(filter(None, (prior_notes, note)))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_text(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def parse_stringtable(text: str) -> tuple[list[StringEntry], list[dict]]:
    entries: list[StringEntry] = []
    malformed: list[dict] = []
    for line_no, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.lstrip("\ufeff")
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        match = re.match(r"^(\S+)\s+(.*)$", line)
        if not match:
            # Empty values occur in the shipped tables and are valid.
            if re.match(r"^\S+$", stripped):
                entries.append(StringEntry(stripped, "", line_no))
            else:
                malformed.append({"line": line_no, "text": raw_line})
            continue
        entries.append(StringEntry(match.group(1), match.group(2).rstrip(), line_no))
    return entries, malformed


def namespace_for(filename: str) -> str:
    return PurePosixPath(filename).stem.removesuffix("_en")


HON_CONTROL_RE = re.compile(r"\^(?:[0-9]{3}|[^\s])")


def canonical_term(value: str) -> str:
    value = HON_CONTROL_RE.sub("", value)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", value).strip(" *\t\r\n")


def entity_owner(key: str) -> str:
    match = re.match(r"^(?:Hero|Ability|Item)_([^_:]+)", key, re.I)
    if not match:
        return ""
    owner = match.group(1)
    if key.lower().startswith("ability_"):
        owner = re.sub(r"\d+[a-z]?$", "", owner, flags=re.I)
    return owner.lower()


def assign_protected_terms(rows: list[dict]) -> None:
    """Attach context-aware canonical terms using longest non-overlapping match."""
    canonical: list[dict] = []
    for row in rows:
        if row["category"] not in {"hero_name", "ability_name", "item_name", "announcer_event"}:
            continue
        term = canonical_term(row["english"])
        if len(term) < 3 or not re.search(r"[A-Za-z]", term):
            continue
        canonical.append({"term": term, "category": row["category"], "owner": entity_owner(row["key"])})

    identities: dict[str, list[dict]] = defaultdict(list)
    for item in canonical:
        identities[item["term"]].append(item)

    if not identities:
        return
    # One longest-first combined matcher keeps the operation linear in catalog
    # text size instead of compiling thousands of regexes per row.
    alternatives = "|".join(re.escape(term) for term in sorted(identities, key=lambda value: (-len(value), value)))
    matcher = re.compile(rf"(?<![A-Za-z0-9])(?:{alternatives})(?![A-Za-z0-9])")

    for row in rows:
        row["protected_terms"] = []
        if row["runtime_role"] != "DISPLAY_TEXT" or row["status"] in {"KEEP_EN", "DEPRECATED", "DYNAMIC"}:
            continue
        owner = entity_owner(row["key"])
        selected: list[str] = []
        for match in matcher.finditer(row["english"]):
            term = match.group(0)
            allowed = any(
                (owner and owner == item["owner"])
                or item["category"] in {"hero_name", "announcer_event"}
                or (item["category"] in {"ability_name", "item_name"} and (" " in term or len(term) >= 8))
                for item in identities[term]
            )
            if allowed:
                selected.append(term)
        row["protected_terms"] = list(dict.fromkeys(selected))


STRUCTURAL_ESCAPE_RE = re.compile(r"^(?:\\[rnt])+$")
NAME_FIELD_RE = re.compile(r"(?:^|_)(?:name|displayname|display_name)(?::[^:]*)?$", re.I)
RESOURCE_VALUE_RE = re.compile(
    r"^(?:[A-Za-z]:[\\/]|[./\\]).*|^\S+\.(?:tga|dds|png|webp|jpg|model|effect|material|wav|ogg|mp3|xml|lua)$",
    re.I,
)
COSMETIC_TOKEN_RE = re.compile(
    r"(?:^|_)(?:altavatars?|avatars?|skins?|couriers?|wards?|emotes?|kill_effects?|voice_?packs?|product)(?:_|$)",
    re.I,
)


def classify(namespace: str, key: str, english: str) -> tuple[str, str, str, str, str]:
    """Return category, context, status, protected_reason, runtime_role.

    Rules are intentionally conservative. Unknown entity records go to REVIEW.
    """
    k = key.lower()
    e = english.strip()

    if not e:
        return "empty", "Empty upstream value", "DEPRECATED", "", "STRUCTURAL"
    if STRUCTURAL_ESCAPE_RE.fullmatch(e):
        return "structural_value", "Escape-only runtime structure", "KEEP_EN", "Structural escape sequence must remain exact", "STRUCTURAL"
    if re.fullmatch(r"(?:https?://|www\.)\S+", e, flags=re.I):
        return "external_content", "URL or external target", "DYNAMIC", "", "DYNAMIC_DATA"

    if namespace == "game_messages":
        return "game_event_feed", "First-pass safe English clone", "KEEP_EN", "Game event feed protected pending key-by-key review", "DISPLAY_TEXT"

    # Event identity keys are protected by their namespace grammar. Words such
    # as Victory, Immortal or Payback are never globally blacklisted.
    if namespace == "interface" and re.fullmatch(r"announcement_[a-z0-9_]+", k):
        return "announcer_event", "Branded announcer event identity", "KEEP_EN", "Announcer event identity stays English", "DISPLAY_TEXT"

    if re.search(r"item_.*_search_terms(?::.*)?$", k):
        return "search_metadata", "Internal item search index", "REVIEW", "", "SEARCH_METADATA"
    if re.search(r"item_.*_shop_categories(?::.*)?$", k):
        return "shop_metadata", "Internal shop Filter_* identifiers", "REVIEW", "", "INTERNAL_ID"
    if re.fullmatch(r"(?:filter_[A-Za-z0-9_]+)(?:,(?:filter_[A-Za-z0-9_]+))*", e, flags=re.I):
        return "internal_filter", "Internal Filter_* identifier", "REVIEW", "", "INTERNAL_ID"

    if namespace == "client_messages" and k.startswith("chat_command_"):
        message_suffix = re.search(
            r"_(?:help|info|usage|failed|failure|success|error|on|off|result|message|tip|description)(?::.*)?$",
            k,
        )
        token_value = bool(re.fullmatch(r"/?[A-Za-z][A-Za-z0-9_-]*", e))
        if not message_suffix and (k.endswith("_short") or token_value):
            return "chat_command_token", "Command, alias or subcommand token", "REVIEW", "", "COMMAND_TOKEN"
        return "chat_command_help", "Command help, usage or result prose", "TRANSLATE", "", "DISPLAY_TEXT"

    if RESOURCE_VALUE_RE.fullmatch(e):
        return "resource_path", "Runtime resource or filesystem path", "REVIEW", "", "RESOURCE_PATH"

    nameish = bool(NAME_FIELD_RE.search(key))
    hero = bool(re.match(r"^Hero_", key, re.I))
    ability = bool(re.match(r"^(?:Ability_|Gadget_.*_Ability)", key, re.I))
    item = bool(re.match(r"^Item_", key, re.I))
    description = any(token in k for token in (
        "description", "_desc", "tooltip", "flavor", "effect", "details", "_role",
    ))

    if nameish and ability:
        return "ability_name", "Ability display name or named variant", "KEEP_EN", "Ability names stay English", "DISPLAY_TEXT"
    if nameish and item:
        return "item_name", "Item display name or named variant", "KEEP_EN", "Item names stay English", "DISPLAY_TEXT"
    if nameish and hero:
        return "hero_name", "Hero display name", "KEEP_EN", "Hero names stay English", "DISPLAY_TEXT"
    if hero and re.search(r"_(?:description|role)(?::.*)?$", k):
        return "hero_description", "Hero description or gameplay role prose", "TRANSLATE", "", "DISPLAY_TEXT"
    if description and (hero or ability or item):
        category = "ability_description" if ability else "item_description" if item else "hero_description"
        return category, "Gameplay description", "TRANSLATE", "", "DISPLAY_TEXT"

    # Cosmetics use structured underscore-delimited tokens. Entity/item/ability
    # grammar above takes precedence, preventing EmeraldWarden and WardOfSight
    # from becoming cosmetic matches.
    if nameish and COSMETIC_TOKEN_RE.search(key):
        return "cosmetic_name", "Named cosmetic product", "KEEP_EN", "Cosmetic product names stay English", "DISPLAY_TEXT"

    if namespace == "entities":
        if description:
            return "gameplay_description", "Entity description or tooltip", "TRANSLATE", "", "DISPLAY_TEXT"
        return "entity_review", "Entity value requires semantic review", "REVIEW", "", "DISPLAY_TEXT"

    if any(token in k for token in ("option", "setting", "slider", "volume", "graphics", "sound", "control")):
        return "settings_ui", "Settings/options UI", "TRANSLATE", "", "DISPLAY_TEXT"
    if any(token in k for token in ("help", "tutorial", "learn")):
        return "help_tutorial", "Help or tutorial prose", "TRANSLATE", "", "DISPLAY_TEXT"
    if any(token in k for token in ("profile", "match_history", "ladder", "leaderboard")):
        return "profile_competitive_ui", "Profile, history or ranking UI", "TRANSLATE", "", "DISPLAY_TEXT"
    if any(token in k for token in ("button", "general_", "label", "dialog", "popup", "notification")):
        return "functional_ui", "Functional interface", "TRANSLATE", "", "DISPLAY_TEXT"
    return "functional_ui", f"{namespace} string table", "TRANSLATE", "", "DISPLAY_TEXT"


def should_extract(name: str) -> bool:
    low = name.lower()
    if name in EXTRACT_EXACT:
        return True
    if low.startswith("stringtables/"):
        return True
    if low.startswith("preact/src/") or low.startswith("preact-remote/src/"):
        return PurePosixPath(low).suffix in TEXT_EXTENSIONS
    if low.startswith("preact/preact-qjs/") or low.startswith("preact/public/"):
        return True
    if low in {
        "preact/package.json", "preact/package-lock.json", "preact/bun.lock",
        "preact/tsconfig.json", "preact/tsconfig.app.json", "preact/vite.config.ts",
        "preact/vite-env.d.ts", "preact/global.d.ts", "preact/index.html",
        "preact/sciter.js", "preact/readme.md",
        "preact-remote/package.json", "preact-remote/tsconfig.json",
        "preact-remote/vite.config.ts",
    }:
        return True
    return False


def is_relevant(info: zipfile.ZipInfo) -> bool:
    low = info.filename.lower()
    ext = PurePosixPath(low).suffix
    return ext in TEXT_EXTENSIONS and (
        any(term in low for term in RELEVANT_TERMS)
        or low.startswith(("ui/", "preact/", "preact-remote/", "stringtables/"))
    )


def safe_extract(zf: zipfile.ZipFile, info: zipfile.ZipInfo, root: Path) -> None:
    parts = PurePosixPath(info.filename).parts
    if info.is_dir() or not parts or any(part in ("", ".", "..") for part in parts):
        return
    target = root.joinpath(*parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(zf.read(info))


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def preact_layer(name: str) -> str:
    match = re.search(r"/layers/([^/]+)/", name)
    if match:
        return match.group(1)
    if name.startswith("preact-remote/"):
        return "motd_remote"
    if "/components/" in name:
        return "shared_component"
    if "/apis/" in name or "/services/" in name:
        return "api"
    return "app_shell"


def native_ui_area(name: str) -> str:
    low = name.lower()
    if "/dev/" in low:
        return "developer_ui"
    for token, area in (
        ("matchmaking", "matchmaking"), ("team_builder", "matchmaking"),
        ("game_lobby", "lobby"), ("lobby", "lobby"),
        ("hero_select", "hero_select"), ("heroselect", "hero_select"),
        ("shop", "shop"), ("replay", "replay"), ("postgame", "postgame"),
        ("endgame", "postgame"), ("hud", "hud"), ("loading", "loading"),
        ("tutorial", "tutorial"), ("help", "help"), ("confirmation", "dialogs"),
        ("dialog", "dialogs"), ("options", "settings"), ("profile", "profile"),
    ):
        if token in low:
            return area
    return "native_ui_other"


def plausible_native_visible(value: str) -> bool:
    value = html.unescape(re.sub(r"\s+", " ", value).strip())
    if not (2 <= len(value) <= 500) or not re.search(r"[A-Za-z]", value):
        return False
    if re.search(r"(?:Translate|Locali[sz]e|GetLocalizedString)\s*\(", value, re.I):
        return False
    if value.startswith(("/", "./", "../", "http://", "https://", "$", "#", "^")):
        return False
    if RESOURCE_VALUE_RE.fullmatch(value) or re.search(r"\.(?:tga|dds|png|xml|lua|interface|package)\b", value, re.I):
        return False
    if re.fullmatch(r"[a-z][a-z0-9_.:-]*", value):
        return False
    if re.fullmatch(r"\{[^{}]+\}", value) or re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*_[A-Za-z0-9_]+", value):
        return False
    if any(token in value for token in ("==", "!=", "&&", "||", "UICmd", "GetCvar", "SetCvar")):
        return False
    return True


def scan_native_ui_file(name: str, text: str) -> tuple[list[dict], list[dict]]:
    candidates: list[dict] = []
    integrations: list[dict] = []
    seen: set[tuple[int, str, str]] = set()

    patterns = [
        ("visible_attribute", re.compile(
            r"\b(text|label|title|tooltip|caption|description|header)\s*=\s*([\"'])(.*?)\2",
            re.I,
        )),
        ("visible_setter", re.compile(
            r"\b(SetText|SetLabel|SetTooltip|SetTitle|SetCaption)\s*\(\s*([\"'])(.*?)\2",
            re.I,
        )),
        ("text_node", re.compile(r">\s*([^<>{}\r\n]*[A-Za-z][^<>{}\r\n]*)\s*</")),
    ]
    for kind, pattern in patterns:
        for match in pattern.finditer(text):
            value_group = 3 if kind != "text_node" else 1
            value = html.unescape(re.sub(r"\s+", " ", match.group(value_group)).strip())
            if not plausible_native_visible(value):
                continue
            line = line_number(text, match.start(value_group))
            marker = (line, value, kind)
            if marker in seen:
                continue
            seen.add(marker)
            candidates.append({
                "literal": value, "source_file": name, "source_line": line,
                "kind": kind, "area": native_ui_area(name), "status": "REVIEW",
                "runtime_role": "DISPLAY_TEXT",
                "notes": "Hardcoded visible-text candidate; confirm runtime path",
            })

    integration_patterns = {
        # Generic GetString/GetText methods are mostly cvar/widget accessors in
        # HoN Lua.  Count only APIs whose name establishes localization intent.
        "localization_call": re.compile(r"(?:Translate|Locali[sz]e|GetLocalizedString)\s*\(", re.I),
        "localization_key_attribute": re.compile(
            r"\b(?:text|label|title|tooltip|caption|description)\s*=\s*[\"']([a-z][a-z0-9_]{3,})[\"']",
            re.I,
        ),
    }
    lines = text.splitlines()
    for kind, pattern in integration_patterns.items():
        for match in pattern.finditer(text):
            line = line_number(text, match.start())
            integrations.append({
                "kind": kind, "source_file": name, "source_line": line,
                "area": native_ui_area(name), "excerpt": lines[line - 1].strip()[:500],
            })
    return candidates, integrations


def plausible_human_text(value: str) -> bool:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) < 2 or len(value) > 500 or not re.search(r"[A-Za-z]", value):
        return False
    if value.startswith(("/", "./", "../", "http://", "https://", "data:")):
        return False
    if re.fullmatch(r"[a-z0-9_.:/@-]+", value):
        return False
    if any(token in value for token in ("${", "=>", "import ", "className", "--")):
        return False
    if re.match(r"^M\d", value) and re.search(r"\d", value):
        return False
    if re.fullmatch(r"(?:rgba?|hsla?)\([^)]*\)", value, flags=re.I):
        return False
    tokens = value.split()
    if tokens and all(re.fullmatch(r"[a-z][a-z0-9_-]*", token) for token in tokens):
        return False
    return " " in value or bool(re.search(r"[A-Z][a-z]", value))


def scan_preact_file(name: str, text: str) -> tuple[list[dict], list[dict]]:
    candidates: list[dict] = []
    integration_hits: list[dict] = []
    seen: set[tuple[int, str, str]] = set()

    if re.search(r"/(?:mock|mockdata)\.(?:ts|tsx|js|jsx)$", name, flags=re.I):
        return [], []

    patterns = [
        ("jsx_text", re.compile(r">([^<>{}\r\n]*[A-Za-z][^<>{}\r\n]*)</")),
        ("ui_attribute", re.compile(r"(?:aria-label|title|placeholder|alt)\s*=\s*[\"']([^\"']+)[\"']", re.I)),
        ("string_literal", re.compile(r"(?<![A-Za-z0-9_])[\"']([^\"'\r\n]{2,500})[\"']")),
    ]
    for kind, pattern in patterns:
        for match in pattern.finditer(text):
            value = re.sub(r"\s+", " ", match.group(1)).strip()
            if not plausible_human_text(value):
                continue
            line = line_number(text, match.start(1))
            source_line = text.splitlines()[line - 1].strip()
            if source_line.startswith(("//", "*", "/*")):
                continue
            prefix_on_line = text[text.rfind("\n", 0, match.start(1)) + 1:match.start(1)]
            if "//" in prefix_on_line or "console." in source_line:
                continue
            if kind == "string_literal" and " " not in value:
                continue
            if kind == "string_literal" and any(
                row["source_line"] == line and row["literal"] == value for row in candidates
            ):
                continue
            marker = (line, value, kind)
            if marker in seen:
                continue
            seen.add(marker)
            candidates.append({
                "literal": value,
                "source_file": name,
                "source_line": line,
                "kind": kind,
                "layer": preact_layer(name),
                "status": "TRANSLATE",
                "notes": "Hardcoded client-side candidate; verify render path",
            })

    for pattern_name, pattern in {
        "localization_api": re.compile(r"(?:locali[sz]e|GetString|GetText)\s*\(|\bi18n\b", re.I),
        "network_content": re.compile(r"fetch\s*\(|/v\d+/|https?://", re.I),
        "image_asset": re.compile(r"[\"'][^\"']+\.(?:png|webp|jpg|jpeg|dds|tga)[\"']", re.I),
    }.items():
        for match in pattern.finditer(text):
            integration_hits.append({
                "kind": pattern_name,
                "source_file": name,
                "source_line": line_number(text, match.start()),
                "excerpt": text.splitlines()[line_number(text, match.start()) - 1].strip()[:500],
            })
    return candidates, integration_hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--juvio-root", type=Path, required=True)
    args = parser.parse_args()

    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required for ZIP Zstandard method 93")

    project = args.project_root.resolve()
    juvio = args.juvio_root.resolve()
    archive = juvio / "heroes of newerth" / "resources0.jz"
    extension_archive = juvio / "extensions" / "resources0.jz"
    if not archive.is_file():
        raise SystemExit(f"Archive not found: {archive}")

    for name in ("catalog", "reports", "src", "tools", "docs", "tests", "build", "backups", "scripts", "translations"):
        (project / name).mkdir(parents=True, exist_ok=True)

    digest = sha256_file(archive)
    stat = archive.stat()
    snapshot_root = project / "src" / "upstream" / digest[:12]
    generated_at = datetime.now(timezone.utc).isoformat()

    inventory: list[dict] = []
    relevant: list[dict] = []
    method_counts: Counter[int] = Counter()
    method_sizes: Counter[int] = Counter()
    tables: dict[str, tuple[list[StringEntry], list[dict]]] = {}
    preact_candidates: list[dict] = []
    preact_integrations: list[dict] = []
    preact_file_counts: Counter[str] = Counter()
    native_ui_candidates: list[dict] = []
    native_ui_integrations: list[dict] = []
    native_ui_file_counts: Counter[str] = Counter()

    with zipfile.ZipFile(archive, "r") as zf:
        infos = zf.infolist()
        for info in infos:
            row = {
                "path": info.filename,
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "compression_method": info.compress_type,
                "crc32": f"{info.CRC:08x}",
                "is_dir": info.is_dir(),
            }
            inventory.append(row)
            method_counts[info.compress_type] += 1
            method_sizes[info.compress_type] += info.file_size
            if is_relevant(info):
                relevant.append(row)
            if should_extract(info.filename):
                safe_extract(zf, info, snapshot_root)

            low = info.filename.lower()
            if low.startswith("stringtables/") and low.endswith(("_en.str", "_th.str")):
                tables[info.filename] = parse_stringtable(decode_text(zf.read(info)))
            if (low.startswith("preact/src/") or low.startswith("preact-remote/src/")) and low.endswith((".ts", ".tsx", ".js", ".jsx")):
                text = decode_text(zf.read(info))
                found, integrations = scan_preact_file(info.filename, text)
                preact_candidates.extend(found)
                preact_integrations.extend(integrations)
                preact_file_counts[preact_layer(info.filename)] += 1
            if low.startswith("ui/") and low.endswith((".package", ".interface", ".lua")):
                text = decode_text(zf.read(info))
                found, integrations = scan_native_ui_file(info.filename, text)
                native_ui_candidates.extend(found)
                native_ui_integrations.extend(integrations)
                native_ui_file_counts[PurePosixPath(low).suffix] += 1

    extension_info: dict | None = None
    if extension_archive.is_file():
        with zipfile.ZipFile(extension_archive, "r") as ext:
            extension_info = {
                "path": str(extension_archive),
                "size": extension_archive.stat().st_size,
                "sha256": sha256_file(extension_archive),
                "entry_count": len(ext.infolist()),
                "entries": [i.filename for i in ext.infolist()],
                "compression_methods": dict(Counter(str(i.compress_type) for i in ext.infolist())),
            }

    build_info = {
        "generated_at_utc": generated_at,
        "juvio_root": str(juvio),
        "archive_path": str(archive),
        "archive_size": stat.st_size,
        "archive_mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": digest,
        "known_sha256": KNOWN_SHA256,
        "matches_known_sha256": digest == KNOWN_SHA256,
        "entry_count": len(inventory),
        "compression_methods": {
            str(method): {"entries": method_counts[method], "uncompressed_bytes": method_sizes[method]}
            for method in sorted(method_counts)
        },
        "existing_extension": extension_info,
    }
    write_json(project / "reports" / "build.json", build_info)
    write_jsonl(project / "reports" / "archive_inventory.jsonl", inventory)
    write_json(project / "reports" / "relevant_resources.json", {
        "criteria": {"extensions": sorted(TEXT_EXTENSIONS), "path_terms": list(RELEVANT_TERMS)},
        "count": len(relevant),
        "entries": relevant,
    })

    catalog_rows: list[dict] = []
    missing_thai: list[dict] = []
    table_stats: list[dict] = []
    duplicates_report: list[dict] = []
    malformed_report: list[dict] = []

    en_names = sorted(name for name in tables if name.endswith("_en.str"))
    for en_name in en_names:
        ns = namespace_for(en_name)
        th_name = en_name.removesuffix("_en.str") + "_th.str"
        en_entries, en_malformed = tables[en_name]
        th_entries, th_malformed = tables.get(th_name, ([], []))
        # The shipped files contain duplicate keys. HoN effectively resolves one
        # value per key; use the final occurrence and report every duplicate.
        en_effective = list({entry.key: entry for entry in en_entries}.values())
        th_effective = list({entry.key: entry for entry in th_entries}.values())
        th_by_key = {entry.key: entry.value for entry in th_effective}
        en_counts = Counter(entry.key for entry in en_entries)
        th_counts = Counter(entry.key for entry in th_entries)
        for key, count in en_counts.items():
            if count > 1:
                duplicates_report.append({"source_file": en_name, "key": key, "count": count})
        for key, count in th_counts.items():
            if count > 1:
                duplicates_report.append({"source_file": th_name, "key": key, "count": count})
        malformed_report.extend({"source_file": en_name, **row} for row in en_malformed)
        malformed_report.extend({"source_file": th_name, **row} for row in th_malformed)

        for entry in en_effective:
            category, context, status, reason, runtime_role = classify(ns, entry.key, entry.value)
            assert status in STATUS_VALUES
            thai = th_by_key.get(entry.key, "")
            if entry.key not in th_by_key:
                thai_signal = "MISSING"
            elif thai == entry.value:
                thai_signal = "SAME_AS_ENGLISH"
            elif not thai:
                thai_signal = "EMPTY"
            else:
                thai_signal = "DIFFERENT"
            row = {
                "id": f"{ns}:{entry.key}",
                "key": entry.key,
                "english": entry.value,
                "thai": thai,
                "source_file": en_name,
                "source_line": entry.line,
                "namespace": ns,
                "category": category,
                "context": context,
                "status": status,
                "runtime_role": runtime_role,
                "thai_signal": thai_signal,
                "protected_reason": reason,
                "protected_terms": [],
                "locked_spans": [],
                "russian": entry.value if status == "KEEP_EN" else "",
                "notes": "",
                "english_hash": hashlib.sha256(entry.value.encode("utf-8")).hexdigest(),
                "classification_version": 2,
                "classification_source": "AUTO",
            }
            catalog_rows.append(row)
            if entry.key not in th_by_key:
                missing_thai.append({
                    "namespace": ns, "key": entry.key, "english": entry.value,
                    "source_file": en_name, "source_line": entry.line,
                })

        table_stats.append({
            "namespace": ns,
            "english_file": en_name,
            "thai_file": th_name if th_name in tables else None,
            "english_entries": len(en_entries),
            "english_unique_entries": len(en_effective),
            "thai_entries": len(th_entries),
            "thai_unique_entries": len(th_effective),
            "missing_thai_keys": sum(1 for e in en_effective if e.key not in th_by_key),
            "thai_only_keys": sum(1 for e in th_effective if e.key not in en_counts),
        })

    assign_protected_terms(catalog_rows)

    catalog_path = project / "catalog" / "strings.jsonl"
    previous_rows = {row.get("id"): row for row in read_jsonl(catalog_path) if row.get("id")}
    update_counts: Counter[str] = Counter()
    current_ids: set[str] = set()
    human_fields = (
        "category", "context", "status", "runtime_role", "protected_reason",
        "protected_terms", "locked_spans", "russian", "notes", "classification_source",
    )
    for row in catalog_rows:
        row_id = row["id"]
        current_ids.add(row_id)
        previous = previous_rows.get(row_id)
        if previous is None:
            update_counts["new"] += 1
            continue
        if previous.get("english_hash") == row["english_hash"]:
            update_counts["unchanged"] += 1
            if previous.get("classification_source") == "HUMAN" and row["status"] != "KEEP_EN":
                for field in human_fields:
                    if field in previous:
                        row[field] = previous[field]
            else:
                # Preserve actual translator work, but clear English values that
                # existed only because an old AUTO rule incorrectly used KEEP_EN.
                prior_russian = previous.get("russian", "")
                prior_was_auto_keep = (
                    previous.get("status") == "KEEP_EN"
                    and previous.get("classification_source", "AUTO") == "AUTO"
                    and prior_russian == previous.get("english", "")
                    and row["status"] != "KEEP_EN"
                )
                if row["status"] == "KEEP_EN":
                    row["russian"] = row["english"]
                elif not prior_was_auto_keep:
                    row["russian"] = prior_russian
                row["notes"] = previous.get("notes", row["notes"])
            continue

        update_counts["english_changed"] += 1
        merge_english_changed(row, previous)

    removed_rows = [previous_rows[row_id] for row_id in sorted(previous_rows.keys() - current_ids)]
    update_counts["removed"] = len(removed_rows)
    write_json(project / "reports" / "catalog_update.json", {
        "counts": dict(sorted(update_counts.items())),
        "removed": removed_rows,
    })

    write_jsonl(catalog_path, catalog_rows)
    write_csv(project / "catalog" / "strings.csv", CATALOG_FIELDS, catalog_rows)
    write_csv(project / "reports" / "missing_thai.csv", ["namespace", "key", "english", "source_file", "source_line"], missing_thai)

    status_counts = Counter(row["status"] for row in catalog_rows)
    category_counts = Counter(row["category"] for row in catalog_rows)
    namespace_counts = Counter(row["namespace"] for row in catalog_rows)
    runtime_role_counts = Counter(row["runtime_role"] for row in catalog_rows)
    thai_signal_counts = Counter(row["thai_signal"] for row in catalog_rows)
    diagnostic = [row for row in catalog_rows if row["key"] == "options_slider_max_ui_framerate"]
    write_json(project / "reports" / "stringtable_stats.json", {
        "total_catalog_rows": len(catalog_rows),
        "tables": table_stats,
        "by_status": dict(sorted(status_counts.items())),
        "by_category": dict(sorted(category_counts.items())),
        "by_namespace": dict(sorted(namespace_counts.items())),
        "by_runtime_role": dict(sorted(runtime_role_counts.items())),
        "by_thai_signal": dict(sorted(thai_signal_counts.items())),
        "duplicate_keys": duplicates_report,
        "malformed_lines": malformed_report,
        "diagnostic_key": diagnostic,
    })

    preact_candidates.sort(key=lambda r: (r["source_file"], r["source_line"], r["literal"]))
    preact_integrations.sort(key=lambda r: (r["source_file"], r["source_line"], r["kind"]))
    write_jsonl(project / "reports" / "preact_string_candidates.jsonl", preact_candidates)
    write_csv(project / "reports" / "preact_string_candidates.csv", PREACT_FIELDS, preact_candidates)
    write_json(project / "reports" / "preact_integration_points.json", {
        "source_files_by_layer": dict(sorted(preact_file_counts.items())),
        "candidate_count": len(preact_candidates),
        "candidate_count_by_layer": dict(sorted(Counter(r["layer"] for r in preact_candidates).items())),
        "candidate_count_by_kind": dict(sorted(Counter(r["kind"] for r in preact_candidates).items())),
        "integration_hits": preact_integrations,
    })

    native_ui_candidates.sort(key=lambda r: (r["source_file"], r["source_line"], r["literal"]))
    native_ui_integrations.sort(key=lambda r: (r["source_file"], r["source_line"], r["kind"]))
    write_jsonl(project / "reports" / "native_ui_string_candidates.jsonl", native_ui_candidates)
    write_json(project / "reports" / "native_ui_integration_points.json", {
        "scan_scope": "Direct read-only scan of ui/**/*.package, ui/**/*.interface and ui/**/*.lua in resources0.jz",
        "files_by_extension": dict(sorted(native_ui_file_counts.items())),
        "candidate_count": len(native_ui_candidates),
        "candidate_count_by_area": dict(sorted(Counter(r["area"] for r in native_ui_candidates).items())),
        "candidate_count_by_kind": dict(sorted(Counter(r["kind"] for r in native_ui_candidates).items())),
        "integration_count_by_kind": dict(sorted(Counter(r["kind"] for r in native_ui_integrations).items())),
        "integration_hits": native_ui_integrations,
    })

    print(json.dumps({
        "build": build_info,
        "catalog_rows": len(catalog_rows),
        "missing_thai": len(missing_thai),
        "catalog_by_status": dict(sorted(status_counts.items())),
        "preact_candidates": len(preact_candidates),
        "snapshot_root": str(snapshot_root),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
