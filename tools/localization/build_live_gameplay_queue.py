#!/usr/bin/env python3
"""Build the translation priority queue from the live HoN roster and CURRENT data.

This tool is deliberately read-only with respect to Juvio. It downloads the
official hero/item inventories, reads CURRENT English strings directly from the
installed upstream archive, and writes project-side JSON/JSONL reports only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_UPSTREAM = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Juvio" / "heroes of newerth" / "resources0.jz"
HEROES_URL = "https://gamedata.juvio.com/entities/heroes"
ITEMS_URL = "https://gamedata.juvio.com/entities/items"
ENTITY_TABLE = "stringtables/entities_en.str"
OUTPUT_DIR = ROOT / "translation" / "priority"
CACHE_DIR = ROOT / "translation" / "cache" / "live"
CONTEXT_DIR = ROOT / "translation" / "context" / "live"

DESCRIPTION_SUFFIXES = (
    "_description", "_description2", "_description_simple", "_effect",
    "_FRAME_effect", "_IMPACT_effect", "_ATTACK_IMPACT_effect",
    "_effect_header", "_effect_header2",
)
EXCLUDED_PARTS = ("_shop_flavor", "_tooltip_flavor", "_search_terms", "_shop_categories")
STRUCTURAL_RE = re.compile(r"\{[^{}]+\}|%\d*\$?[sdif]|#[A-Za-z0-9_]+#|\^(?:[!*]|[A-Za-z]|\d{3})|</?[A-Za-z][^>]*>")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_json(url: str) -> tuple[dict[str, Any], str]:
    request = urllib.request.Request(url, headers={"User-Agent": "HoN-Reborn-RU/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
    return json.loads(raw), sha256_bytes(raw)


def fetch_json_cached(
    url: str, cache_path: Path, *, refresh: bool = False, offline: bool = False,
) -> tuple[dict[str, Any], str, str]:
    """Return API JSON with a durable project-side cache and safe fallback."""
    if cache_path.exists() and not refresh:
        raw = cache_path.read_bytes()
        return json.loads(raw), sha256_bytes(raw), "cache"
    if offline:
        raise SystemExit(f"Offline cache is missing: {cache_path}")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "HoN-Reborn-RU/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except Exception:
        if not cache_path.exists():
            raise
        raw = cache_path.read_bytes()
        return json.loads(raw), sha256_bytes(raw), "stale-cache-fallback"
    payload = json.loads(raw)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    normalized = cache_path.read_bytes()
    return payload, sha256_bytes(normalized), "network"


def parse_stringtable(raw: bytes) -> dict[str, str]:
    text = raw.decode("utf-8-sig")
    effective: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.lstrip("\ufeff")
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        match = re.match(r"^(\S+)\s+(.*)$", line)
        if match:
            effective[match.group(1)] = match.group(2).rstrip()
        elif re.match(r"^\S+$", stripped):
            effective[stripped] = ""
    return effective


def read_current_entities(upstream: Path) -> dict[str, str]:
    with zipfile.ZipFile(upstream) as archive:
        if archive.testzip() is not None:
            raise SystemExit("CURRENT upstream CRC failed")
        return parse_stringtable(archive.read(ENTITY_TABLE))


def read_current_entities_cached(upstream: Path, cache_dir: Path) -> tuple[dict[str, str], str, str]:
    upstream_sha = sha256_file(upstream)
    cache_path = cache_dir / f"entities_{upstream_sha}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8")), upstream_sha, "cache"
    strings = read_current_entities(upstream)
    write_json(cache_path, strings)
    return strings, upstream_sha, "upstream"


def load_catalog() -> dict[str, dict[str, Any]]:
    path = ROOT / "catalog" / "strings.jsonl"
    rows = (json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line)
    return {row["id"]: row for row in rows}


def load_manual_translations() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for path in sorted((ROOT / "translation" / "human").glob("batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for entry in payload["entries"]:
            for logical_key in entry["keys"]:
                if logical_key in result:
                    raise SystemExit(f"Duplicate manual key: {logical_key}")
                result[logical_key] = {
                    "ru": entry["ru"],
                    "batch_id": payload["batch_id"],
                    "english_hash": entry.get("english_hash", ""),
                }
    return result


def scalar_name(value: Any) -> str | None:
    if isinstance(value, list):
        return str(value[0]) if value else None
    return str(value) if value else None


def is_gameplay_description_key(key: str) -> bool:
    if not key.startswith(("Ability_", "Item_", "State_")):
        return False
    if any(part in key for part in EXCLUDED_PARTS) or key.endswith("_name"):
        return False
    base = key.split(":", 1)[0]
    return any(base.endswith(suffix) for suffix in DESCRIPTION_SUFFIXES)


def structural_tokens(text: str) -> list[str]:
    return STRUCTURAL_RE.findall(text)


def structural_signature(text: str) -> dict[str, Any]:
    return {
        "tokens": dict(Counter(structural_tokens(text))),
        "backslashes": text.count("\\"),
    }


def is_effectively_empty(text: str) -> bool:
    """Treat escaped CR/LF sentinel values as empty localization records."""
    return not re.sub(r"(?:\\[rn]|[\s\uFEFF])+", "", text)


def is_noncontent_record(key: str, text: str) -> bool:
    base = key.split(":", 1)[0]
    return is_effectively_empty(text) or (
        text.strip().casefold() == "none"
        and base.endswith(("_effect_header", "_effect_header2"))
    )


def protected_spans(text: str, terms: Iterable[str]) -> list[str]:
    found = {term for term in terms if term and term in text}
    return sorted(found, key=lambda value: (text.find(value), -len(value), value))


def priority_tier(status: str, scope: str) -> str:
    """P0 repairs, P1 live heroes, P2 live items; P3 is UI/runtime follow-up."""
    if status in {"STALE_REVIEW", "INVALID_REVIEW"}:
        return "P0"
    if scope.startswith("hero"):
        return "P1"
    if scope == "item":
        return "P2"
    return "P3"


def translation_status(logical_key: str, english: str, catalog: dict[str, dict[str, Any]], manual: dict[str, dict[str, str]]) -> str:
    if logical_key not in manual:
        return "TODO"
    approved_hash = manual[logical_key].get("english_hash")
    catalog_row = catalog.get(logical_key)
    current_hash = sha256_bytes(english.encode("utf-8"))
    if approved_hash:
        return "DONE" if approved_hash == current_hash else "STALE_REVIEW"
    if not catalog_row or catalog_row.get("english_hash") != current_hash:
        return "STALE_REVIEW"
    return "DONE"


def build_queue(
    heroes: list[dict[str, Any]], items: list[dict[str, Any]], strings: dict[str, str],
    catalog: dict[str, dict[str, Any]], manual: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    always_protected = {
        "Staff of the Master", "Tier I", "Tier II", "Tier III", "Tier IV", "GPM", "XPM",
    }

    queue: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(scope: str, owner: str, owner_id: int, key: str, ability: str | None = None) -> None:
        logical_key = f"entities:{key}"
        if logical_key in seen or not is_gameplay_description_key(key):
            return
        english = strings[key]
        if is_noncontent_record(key, english):
            return
        seen.add(logical_key)
        status = translation_status(logical_key, english, catalog, manual)
        previous = manual.get(logical_key)
        ru = previous["ru"] if previous else ""
        catalog_row = catalog.get(logical_key, {})
        # The catalog also labels ability-title homonyms such as ``Release``,
        # ``Lift`` and ``Enter`` as locked spans. In prose these are ordinary
        # verbs and must be translated. Only proper item names and the explicit
        # global protected set are mechanically preserved; hero/ability naming
        # remains a semantic review concern in its context pack.
        catalog_terms = {
            str(span["canonical_text"]) for span in catalog_row.get("locked_spans", [])
            if span.get("canonical_text") and span.get("type") == "ITEM"
        }
        spans = protected_spans(english, always_protected | catalog_terms)
        validation = {
            "structure_matches": not ru or structural_signature(english) == structural_signature(ru),
            "protected_spans_preserved": not ru or all(span in ru for span in spans),
        }
        if status == "DONE" and not all(validation.values()):
            status = "INVALID_REVIEW"
        queue.append({
            "schema_version": 1,
            "priority": 1 if scope == "hero_ability" else 2,
            "priority_tier": priority_tier(status, scope),
            "scope": scope,
            "owner": owner,
            "owner_id": owner_id,
            "ability": ability,
            "logical_key": logical_key,
            "key": key,
            "english": english,
            "english_hash": sha256_bytes(english.encode("utf-8")),
            "status": status,
            "existing_ru": ru,
            "batch_id": previous["batch_id"] if previous else None,
            "protected_spans": spans,
            "structural_tokens": structural_tokens(english),
            "validation": validation,
        })

    for hero in sorted(heroes, key=lambda row: str(row["translatedName"]).casefold()):
        internal = str(hero["name"]).removeprefix("Hero_")
        ability_ids = {scalar_name(hero.get(f"inventory{slot}")) for slot in range(4)}
        ability_ids.discard(None)
        related_abilities = {
            key.rsplit("_", 1)[0] for key in strings
            if key.startswith(f"Ability_{internal}") and key.split(":", 1)[0].endswith("_name")
        } | set(ability_ids)
        for key in sorted(strings):
            if key.startswith(f"Ability_{internal}"):
                ability_id = next((candidate for candidate in sorted(related_abilities, key=len, reverse=True) if key.startswith(candidate)), None)
                ability_display = strings.get(f"{ability_id}_name", "") if ability_id else ""
                add("hero_ability", str(hero["translatedName"]), int(hero["id"]), key, ability_display or ability_id)
            elif key.startswith(f"State_{internal}"):
                add("hero_ability_state", str(hero["translatedName"]), int(hero["id"]), key)

    for item in sorted(items, key=lambda row: str(row["translatedName"]).casefold()):
        item_id = str(item["name"])
        internal = item_id.removeprefix("Item_")
        prefixes = (f"{item_id}_", f"State_{internal}_", f"State_Item_{internal}_")
        for key in sorted(strings):
            if key.startswith(prefixes):
                add("item", str(item["translatedName"]), int(item["id"]), key)

    return sorted(queue, key=lambda row: (row["priority"], row["owner"].casefold(), row["key"]))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_context_packs(
    owners: list[dict[str, Any]], queue: list[dict[str, Any]], scope: str,
) -> list[dict[str, Any]]:
    packs: list[dict[str, Any]] = []
    for owner in sorted(owners, key=lambda row: str(row["translatedName"]).casefold()):
        prefix = "hero" if scope == "hero" else "item"
        rows = [
            row for row in queue
            if row["owner_id"] == int(owner["id"]) and row["scope"].startswith(prefix)
        ]
        counts = Counter(row["status"] for row in rows)
        packs.append({
            "schema_version": 1,
            "scope": scope,
            "owner": owner["translatedName"],
            "owner_id": owner["id"],
            "entity": owner["name"],
            "status_counts": dict(counts),
            "rows": rows,
        })
    return packs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    parser.add_argument("--context-dir", type=Path, default=CONTEXT_DIR)
    parser.add_argument("--refresh", action="store_true", help="Refresh official API cache")
    parser.add_argument("--offline", action="store_true", help="Use API cache only")
    args = parser.parse_args()

    heroes_payload, heroes_sha, heroes_source = fetch_json_cached(
        HEROES_URL, args.cache_dir / "heroes.json", refresh=args.refresh, offline=args.offline,
    )
    items_payload, items_sha, items_source = fetch_json_cached(
        ITEMS_URL, args.cache_dir / "items.json", refresh=args.refresh, offline=args.offline,
    )
    heroes = list(heroes_payload["heroes"])
    items = list(items_payload["items"])
    if len(heroes) < 100 or len({row["name"] for row in heroes}) != len(heroes):
        raise SystemExit("Official hero roster failed sanity checks")
    if len(items) < 100 or len({row["name"] for row in items}) != len(items):
        raise SystemExit("Official item inventory failed sanity checks")

    strings, upstream_sha, entities_source = read_current_entities_cached(args.upstream, args.cache_dir)
    catalog = load_catalog()
    manual = load_manual_translations()
    queue = build_queue(heroes, items, strings, catalog, manual)
    counts = Counter(row["status"] for row in queue)
    scope_counts = {scope: dict(Counter(row["status"] for row in queue if row["scope"].startswith(scope))) for scope in ("hero", "item")}
    owner_progress: list[dict[str, Any]] = []
    for scope, owners in (("hero", heroes), ("item", items)):
        for owner in sorted(owners, key=lambda row: str(row["translatedName"]).casefold()):
            owner_rows = [row for row in queue if row["owner_id"] == int(owner["id"]) and row["scope"].startswith(scope)]
            owner_counts = Counter(row["status"] for row in owner_rows)
            owner_progress.append({
                "schema_version": 1,
                "scope": scope,
                "owner": owner["translatedName"],
                "owner_id": owner["id"],
                "entity": owner["name"],
                "rows": len(owner_rows),
                "done": owner_counts["DONE"],
                "todo": owner_counts["TODO"],
                "stale_review": owner_counts["STALE_REVIEW"],
                "invalid_review": owner_counts["INVALID_REVIEW"],
                "complete": bool(owner_rows) and not any(owner_counts[name] for name in ("TODO", "STALE_REVIEW", "INVALID_REVIEW")),
            })
    next_work = sorted(
        (row for row in queue if row["status"] != "DONE"),
        key=lambda row: (0 if row["status"] in {"STALE_REVIEW", "INVALID_REVIEW"} else 1, row["priority"], row["owner"].casefold(), row["key"]),
    )
    complete_heroes = sum(1 for row in owner_progress if row["scope"] == "hero" and row["complete"])
    complete_items = sum(1 for row in owner_progress if row["scope"] == "item" and row["complete"])
    hero_context = build_context_packs(heroes, queue, "hero")
    item_context = build_context_packs(items, queue, "item")

    snapshot = {
        "schema_version": 1,
        "upstream": {"path": str(args.upstream), "sha256": upstream_sha, "source": entities_source},
        "official_api": {
            "heroes": {"url": HEROES_URL, "sha256": heroes_sha, "count": len(heroes), "source": heroes_source},
            "items": {"url": ITEMS_URL, "sha256": items_sha, "count": len(items), "source": items_source},
        },
        "heroes": [{"id": row["id"], "entity": row["name"], "name": row["translatedName"]} for row in sorted(heroes, key=lambda row: row["translatedName"].casefold())],
        "items": [{"id": row["id"], "entity": row["name"], "name": row["translatedName"]} for row in sorted(items, key=lambda row: row["translatedName"].casefold())],
    }
    report = {
        "schema_version": 1,
        "result": "PASS",
        "upstream_sha256": upstream_sha,
        "active_heroes": len(heroes),
        "active_items": len(items),
        "queue_rows": len(queue),
        "status_counts": dict(counts),
        "scope_status_counts": scope_counts,
        "complete_heroes": complete_heroes,
        "complete_items": complete_items,
        "excluded": ["hero biographies and roles", "hero voice/bot lines", "tooltip/shop flavor", "internal metadata", "entity names"],
        "outputs": {
            "queue": str(args.output_dir / "live_gameplay_queue.jsonl"),
            "next_work": str(args.output_dir / "live_next_work.jsonl"),
            "owner_progress": str(args.output_dir / "live_owner_progress.jsonl"),
            "snapshot": str(args.output_dir / "live_scope_snapshot.json"),
            "hero_context": str(args.context_dir / "hero_context_packs.jsonl"),
            "item_context": str(args.context_dir / "item_context_packs.jsonl"),
        },
    }
    write_jsonl(args.output_dir / "live_gameplay_queue.jsonl", queue)
    write_jsonl(args.output_dir / "live_next_work.jsonl", next_work)
    write_jsonl(args.output_dir / "live_owner_progress.jsonl", owner_progress)
    write_json(args.output_dir / "live_scope_snapshot.json", snapshot)
    write_json(args.output_dir / "live_gameplay_progress.json", report)
    write_jsonl(args.context_dir / "hero_context_packs.jsonl", hero_context)
    write_jsonl(args.context_dir / "item_context_packs.jsonl", item_context)
    for tier in ("P0", "P1", "P2"):
        write_jsonl(
            args.output_dir / f"live_{tier.lower()}_work.jsonl",
            [row for row in next_work if row["priority_tier"] == tier],
        )
    cache_manifest = {
        "schema_version": 1,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "upstream": {"path": str(args.upstream), "sha256": upstream_sha, "source": entities_source},
        "heroes": {"url": HEROES_URL, "sha256": heroes_sha, "count": len(heroes), "source": heroes_source},
        "items": {"url": ITEMS_URL, "sha256": items_sha, "count": len(items), "source": items_source},
    }
    write_json(args.cache_dir / "manifest.json", cache_manifest)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
