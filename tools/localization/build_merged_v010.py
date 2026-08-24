#!/usr/bin/env python3
"""Build the 0.1.0 merged Russian overlay.

Precedence for native string tables:
1. current manually reviewed and controlled translations;
2. structurally compatible text from the pinned full donor translation;
3. the current Russian table (including its English fallback).

The merged tables are exposed as both ``*_ru.str`` and ``*_en.str`` because
some legacy HoN UI paths always resolve the English namespace.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
VERSION = "0.1.0"
CURRENT = ROOT / "build" / "human-ru-current" / "resources0.jz"
CURRENT_REPORT = ROOT / "translation" / "reports" / "human_current_rebase.json"
DONOR = ROOT / "external" / "HoN_RU_Pack" / "bundle"
OUTPUT = ROOT / "build" / "merged-ru-v0.1.0" / "resources0.jz"
REPORT = ROOT / "translation" / "reports" / "merged_ru_v0.1.0.json"
DOMAINS = ("bot_messages", "client_messages", "entities", "game_messages", "interface")
NAME_CATEGORIES = {"hero_name", "ability_name", "item_name", "boss_name", "cosmetic_name"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def structural_tokens(text: str) -> dict[str, list[str]]:
    return {
        "placeholders": sorted(re.findall(r"\{[^{}]+\}|%\d*\$?[sdif]|#[A-Za-z0-9_]+#", text)),
        "colors": sorted(re.findall(r"\^(?:[!*]|[A-Za-z]|\d{3})", text)),
        "markup": sorted(re.findall(r"</?[A-Za-z][^>]*>", text)),
        "backslashes": ["\\"] * text.count("\\"),
    }


def parse_table(data: bytes) -> tuple[list[str], dict[str, str]]:
    text = data.decode("utf-8-sig")
    lines = text.splitlines(keepends=True)
    values: dict[str, str] = {}
    for line in lines:
        body = line.rstrip("\r\n")
        if "\t" not in body or body.lstrip().startswith("//"):
            continue
        key, value = body.split("\t", 1)
        if key:
            values[key] = value
    return lines, values


def render_table(lines: list[str], replacements: dict[str, str]) -> bytes:
    rendered: list[str] = []
    for line in lines:
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        if "\t" not in body or body.lstrip().startswith("//"):
            rendered.append(line)
            continue
        key, value = body.split("\t", 1)
        rendered.append(f"{key}\t{replacements.get(key, value)}{ending}")
    return "".join(rendered).encode("utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def reviewed_keys() -> set[str]:
    result: set[str] = set()
    for path in sorted((ROOT / "translation" / "human").glob("batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for entry in payload.get("entries", []):
            result.update(entry.get("keys", []))
    controlled = ROOT / "translation" / "batches" / "controlled_003_consolidated.jsonl"
    for row in load_jsonl(controlled):
        if row.get("approval_state") == "APPROVED_FOR_CONTROLLED_RUNTIME_QA":
            result.add(row["logical_key"])
    return result


def write_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_ZSTANDARD
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def main() -> int:
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required")
    current_report = json.loads(CURRENT_REPORT.read_text(encoding="utf-8"))
    if current_report.get("result") != "PASS" or sha256(CURRENT) != current_report["output"]["sha256"]:
        raise SystemExit("Current reviewed overlay is not a validated input")

    catalog = {row["id"]: row for row in load_jsonl(ROOT / "catalog" / "strings.jsonl")}
    protected = reviewed_keys()
    members: dict[str, bytes] = {}
    counts: Counter[str] = Counter()
    domain_stats: dict[str, dict[str, int]] = {}

    with zipfile.ZipFile(CURRENT) as source:
        if source.testzip() is not None:
            raise SystemExit("Current overlay CRC failed")
        for name in source.namelist():
            if not name.endswith("/"):
                members[name] = source.read(name)

        for domain in DOMAINS:
            ru_name = f"stringtables/{domain}_ru.str"
            donor_path = DONOR / f"{domain}_en.str"
            if ru_name not in members or not donor_path.is_file():
                raise SystemExit(f"Missing merge input for {domain}")
            lines, current_values = parse_table(members[ru_name])
            _, donor_values = parse_table(donor_path.read_bytes())
            replacements: dict[str, str] = {}
            local = Counter()
            for key, current_value in current_values.items():
                logical = f"{domain}:{key}"
                source_row = catalog.get(logical)
                donor_value = donor_values.get(key)
                choice = current_value
                origin = "current_fallback"
                if logical in protected:
                    origin = "reviewed_current"
                elif source_row and source_row.get("category") in NAME_CATEGORIES:
                    origin = "protected_name"
                elif donor_value and re.search(r"[А-Яа-яЁё]", donor_value):
                    english = source_row.get("english", "") if source_row else ""
                    if not english or structural_tokens(english) == structural_tokens(donor_value):
                        choice = donor_value
                        origin = "full_donor"
                    else:
                        origin = "donor_rejected_structure"
                elif re.search(r"[А-Яа-яЁё]", current_value):
                    origin = "current_translation"
                replacements[key] = choice
                local[origin] += 1
                counts[origin] += 1

            merged = render_table(lines, replacements)
            members[ru_name] = merged
            members[f"stringtables/{domain}_en.str"] = merged
            domain_stats[domain] = dict(sorted(local.items()))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.building")
    temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(temporary, "w", allowZip64=True) as archive:
        for name, data in sorted(members.items()):
            write_member(archive, name, data)
    temporary.replace(OUTPUT)

    with zipfile.ZipFile(OUTPUT) as built:
        corrupt = built.testzip()
        names = [name for name in built.namelist() if not name.endswith("/")]
    errors: list[dict[str, object]] = []
    if corrupt:
        errors.append({"code": "CRC_FAILURE", "member": corrupt})
    for domain in DOMAINS:
        if f"stringtables/{domain}_ru.str" not in names or f"stringtables/{domain}_en.str" not in names:
            errors.append({"code": "LOCALE_ALIAS_MISSING", "domain": domain})

    report = {
        "schema_version": 1,
        "version": VERSION,
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "precedence": ["reviewed_current", "protected_name", "full_donor", "current_translation", "current_fallback"],
        "input": {"current": {"path": str(CURRENT), "sha256": sha256(CURRENT)}, "donor": str(DONOR)},
        "selection_counts": dict(sorted(counts.items())),
        "domain_counts": domain_stats,
        "protected_logical_keys": len(protected),
        "output": {"path": str(OUTPUT), "sha256": sha256(OUTPUT), "size_bytes": OUTPUT.stat().st_size, "members": len(names), "crc": "PASS" if not corrupt else "FAIL"},
        "installed": False,
        "runtime_verified": False,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
