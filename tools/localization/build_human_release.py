#!/usr/bin/env python3
"""Build the cumulative manually reviewed Russian localization layer.

The input is the validated Controlled 003 archive. Human batches contain only
explicit logical keys and reviewed Russian text; CURRENT English remains the
semantic identity used by validation.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "build" / "controlled-003" / "resources0.jz"
UPSTREAM = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Juvio" / "heroes of newerth" / "resources0.jz"
OUTPUT = ROOT / "build" / "human-ru" / "resources0.jz"
REPORT = ROOT / "translation" / "reports" / "human_release_build.json"
EXPECTED_BASE_SHA = "364993376ab1ad7310c0b14d88db93b8a82866479727021496e42f7e600c5bd7"
LIVE_SNAPSHOT = ROOT / "translation" / "priority" / "live_scope_snapshot.json"
MEMBERS = {
    "bot_messages": "stringtables/bot_messages_ru.str",
    "interface": "stringtables/interface_ru.str",
    "game_messages": "stringtables/game_messages_ru.str",
    "client_messages": "stringtables/client_messages_ru.str",
    "entities": "stringtables/entities_ru.str",
}
PROTECTED = ("Staff of the Master", "Tier I", "Tier II", "Tier III", "Tier IV", "GPM", "XPM")
FORBIDDEN = ("Посох Мастера", "посох мастера", "Персонал Мастера", "персонал мастера")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line]


def load_live_entities(upstream_sha: str) -> dict[str, str]:
    path = ROOT / "translation" / "cache" / "live" / f"entities_{upstream_sha}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in payload.items()):
        raise SystemExit(f"Invalid live entity cache: {path}")
    return payload


def load_live_stringtables() -> dict[str, dict[str, str]]:
    tables: dict[str, dict[str, str]] = {}
    with zipfile.ZipFile(UPSTREAM) as archive:
        for domain in MEMBERS:
            member = f"stringtables/{domain}_en.str"
            parsed: dict[str, str] = {}
            for line in archive.read(member).decode("utf-8-sig").splitlines():
                if "\t" not in line or line.lstrip().startswith("//"):
                    continue
                key, value = line.split("\t", 1)
                parsed[key] = value.lstrip("\t")
            tables[domain] = parsed
    return tables


def structural_tokens(text: str) -> dict[str, list[str]]:
    # Match the live queue validator: runtime placeholders, colour/markup tokens
    # and escaped line breaks are structural. Literal prose numbers are semantic
    # content and may legitimately change notation (``.25`` -> ``0,25``) or be
    # written as words in Russian.
    return {
        "placeholders": sorted(re.findall(r"\{[^{}]+\}|%\d*\$?[sdif]|#[A-Za-z0-9_]+#", text)),
        "colors": sorted(re.findall(r"\^(?:[!*]|[A-Za-z]|\d{3})", text)),
        "markup": sorted(re.findall(r"</?[A-Za-z][^>]*>", text)),
        "backslashes": ["\\"] * text.count("\\"),
    }


def write_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_ZSTANDARD
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def apply_rows(data: bytes, rows: list[dict[str, Any]]) -> tuple[bytes, list[dict[str, str]]]:
    targets = {row["key"]: row for row in rows}
    seen = Counter()
    changes: list[dict[str, str]] = []
    lines = data.decode("utf-8-sig").splitlines(keepends=True)
    for index, line in enumerate(lines):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        if "\t" not in body or body.lstrip().startswith("//"):
            continue
        key, old = body.split("\t", 1)
        if key not in targets:
            continue
        seen[key] += 1
        new = targets[key]["ru"]
        if old != new:
            lines[index] = f"{key}\t{new}{ending}"
            changes.append({"logical_key": targets[key]["logical_key"], "old": old, "new": new})
    bad = {key: seen[key] for key in targets if seen[key] != 1}
    if bad:
        raise SystemExit(f"Target occurrence mismatch: {bad}")
    return "".join(lines).encode("utf-8"), changes


def append_missing_keys(data: bytes, rows: list[dict[str, Any]]) -> bytes:
    text = data.decode("utf-8-sig")
    existing = {
        line.split("\t", 1)[0]
        for line in text.splitlines()
        if "\t" in line and not line.lstrip().startswith("//")
    }
    missing = [row for row in rows if row["key"] not in existing]
    if not missing:
        return data
    if text and not text.endswith(("\n", "\r")):
        text += "\n"
    text += "".join(f"{row['key']}\t{row['current_source']}\n" for row in missing)
    return text.encode("utf-8")


def main() -> int:
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required")
    snapshot = json.loads(LIVE_SNAPSHOT.read_text(encoding="utf-8"))
    expected_upstream_sha = snapshot["upstream"]["sha256"]
    if sha256(BASE) != EXPECTED_BASE_SHA or sha256(UPSTREAM) != expected_upstream_sha:
        raise SystemExit("Protected Controlled 003/upstream identity mismatch")

    # catalog/strings.jsonl is regenerated directly from the installed CURRENT
    # archive. The later hybrid source_index is useful for candidate review but
    # can legitimately lag behind a just-released game patch.
    source_rows = load_jsonl(ROOT / "catalog" / "strings.jsonl")
    sources = {row["id"]: row for row in source_rows}
    live_entities = load_live_entities(expected_upstream_sha)
    live_tables = load_live_stringtables()
    expanded: list[dict[str, Any]] = []
    batch_counts: dict[str, int] = {}
    for path in sorted((ROOT / "translation" / "human").glob("batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        count = 0
        for entry in payload["entries"]:
            for logical_key in entry["keys"]:
                source = sources.get(logical_key)
                if logical_key.startswith("entities:"):
                    entity_key = logical_key.removeprefix("entities:")
                    if entity_key in live_entities:
                        current = live_entities[entity_key]
                        source = {
                            "namespace": "entities", "key": entity_key,
                            "english": current,
                            "english_hash": hashlib.sha256(current.encode("utf-8")).hexdigest(),
                        }
                if source is None and ":" in logical_key:
                    domain, key = logical_key.split(":", 1)
                    current = live_tables.get(domain, {}).get(key)
                    if current is not None:
                        source = {
                            "namespace": domain, "key": key,
                            "english": current,
                            "english_hash": hashlib.sha256(current.encode("utf-8")).hexdigest(),
                        }
                if source is None:
                    raise SystemExit(f"Unknown CURRENT key in {path.name}: {logical_key}")
                if source["namespace"] not in MEMBERS:
                    raise SystemExit(f"Unsupported domain in {path.name}: {logical_key}")
                if entry.get("english_hash") and entry["english_hash"] != source["english_hash"]:
                    raise SystemExit(f"CURRENT English hash drift in {path.name}: {logical_key}")
                expanded.append({
                    "batch_id": payload["batch_id"], "logical_key": logical_key,
                    "domain": source["namespace"], "key": source["key"],
                    "current_source": source["english"], "current_source_hash": source["english_hash"],
                    "ru": entry["ru"],
                })
                count += 1
        batch_counts[payload["batch_id"]] = count

    duplicate = [key for key, count in Counter(row["logical_key"] for row in expanded).items() if count > 1]
    errors: list[dict[str, Any]] = []
    if duplicate:
        errors.append({"code": "DUPLICATE_LOGICAL_KEYS", "keys": duplicate})
    for row in expanded:
        src, ru = row["current_source"], row["ru"]
        if structural_tokens(src) != structural_tokens(ru):
            errors.append({"code": "STRUCTURAL_TOKEN_MISMATCH", "key": row["logical_key"], "source": structural_tokens(src), "ru": structural_tokens(ru)})
        for span in PROTECTED:
            if span in src and span not in ru:
                errors.append({"code": "PROTECTED_SPAN_LOST", "key": row["logical_key"], "span": span})
        for forbidden in FORBIDDEN:
            if forbidden in ru:
                errors.append({"code": "FORBIDDEN_ITEM_ALIAS", "key": row["logical_key"], "span": forbidden})
    if errors:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps({"result": "FAIL", "errors": errors}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"result": "FAIL", "errors": errors}, ensure_ascii=False, indent=2))
        return 2

    by_domain = {domain: [] for domain in MEMBERS}
    for row in expanded:
        by_domain[row["domain"]].append(row)
    overrides: dict[str, bytes] = {}
    changes: list[dict[str, str]] = []
    with zipfile.ZipFile(BASE) as base:
        if base.testzip() is not None:
            raise SystemExit("Controlled 003 CRC failed")
        for domain, member in MEMBERS.items():
            baseline = base.read(member)
            baseline = append_missing_keys(baseline, by_domain[domain])
            rendered, domain_changes = apply_rows(baseline, by_domain[domain])
            if domain_changes:
                overrides[member] = rendered
                changes.extend(domain_changes)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        temporary = OUTPUT.with_name(f".{OUTPUT.name}.building")
        if temporary.exists():
            temporary.unlink()
        with zipfile.ZipFile(temporary, "w", allowZip64=True) as target:
            for name in sorted(n for n in base.namelist() if not n.endswith("/")):
                write_member(target, name, overrides.get(name, base.read(name)))
        temporary.replace(OUTPUT)

    with zipfile.ZipFile(OUTPUT) as built:
        corrupt = built.testzip()
        entities = built.read(MEMBERS["entities"]).decode("utf-8-sig")
    for forbidden in FORBIDDEN:
        if forbidden in entities:
            errors.append({"code": "FORBIDDEN_ITEM_ALIAS_IN_FINAL_TABLE", "span": forbidden})
    if corrupt:
        errors.append({"code": "CRC_FAILURE", "member": corrupt})
    result = {
        "schema_version": 1,
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "base": {"path": str(BASE), "sha256": sha256(BASE)},
        "upstream": {"path": str(UPSTREAM), "sha256": sha256(UPSTREAM), "unchanged": True},
        "output": {"path": str(OUTPUT), "sha256": sha256(OUTPUT), "size_bytes": OUTPUT.stat().st_size, "crc": "PASS" if not corrupt else "FAIL"},
        "manual_batches": batch_counts,
        "reviewed_keys": len(expanded),
        "actual_changes": len(changes),
        "changed_members": sorted(overrides),
        "installed": False,
        "runtime_verified": False,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
