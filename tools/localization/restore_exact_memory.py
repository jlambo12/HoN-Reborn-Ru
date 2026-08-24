#!/usr/bin/env python3
"""Restore exact-source translations after a CURRENT catalog regeneration.

This is a provenance-preserving recovery step, not an approval step: only an
identical English literal may recover its previous Russian candidate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEMORIES = (
    ROOT / "translations" / "phase2a_memory.jsonl",
    ROOT / "translations" / "pass_b_memory.jsonl",
)
CATALOGS = {
    "catalog": ROOT / "catalog" / "strings.jsonl",
    "native": ROOT / "catalog" / "native_extended_ui.jsonl",
    "preact": ROOT / "catalog" / "preact_ui.jsonl",
}
REPORT = ROOT / "translation" / "reports" / "exact_memory_restore.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def source_text(row: dict) -> str:
    return row.get("english") or row.get("literal") or ""


def main() -> int:
    candidates: dict[str, set[str]] = {}
    origins: dict[tuple[str, str], set[str]] = {}
    for memory_path in MEMORIES:
        for row in read_jsonl(memory_path):
            english, russian = row.get("english", ""), row.get("russian", "")
            if not english or not russian:
                continue
            expected = row.get("english_hash")
            if expected and expected != hashlib.sha256(english.encode()).hexdigest():
                raise SystemExit(f"Corrupt translation-memory hash: {memory_path.name}")
            candidates.setdefault(english, set()).add(russian)
            origins.setdefault((english, russian), set()).add(memory_path.name)
    consensus = {english: next(iter(values)) for english, values in candidates.items() if len(values) == 1}
    conflicts = {english: sorted(values) for english, values in candidates.items() if len(values) > 1}

    counts: dict[str, dict[str, int]] = {}
    restored_rows: list[dict] = []
    for name, path in CATALOGS.items():
        rows = read_jsonl(path)
        restored = preserved = unresolved = 0
        for row in rows:
            english = source_text(row)
            if row.get("russian"):
                preserved += 1
                continue
            if row.get("status") != "TRANSLATE" or row.get("runtime_role") != "DISPLAY_TEXT":
                continue
            if english in consensus:
                russian = consensus[english]
                row["russian"] = russian
                row["translation_origin"] = "EXACT_SOURCE_MEMORY_RECOVERY"
                row["translation_memory_sources"] = sorted(origins[(english, russian)])
                restored += 1
                restored_rows.append({"catalog": name, "id": row["id"], "english": english, "russian": russian})
            else:
                unresolved += 1
        write_jsonl(path, rows)
        counts[name] = {"restored": restored, "preserved": preserved, "unresolved_translatable": unresolved}

    result = {
        "schema_version": 1,
        "result": "PASS",
        "rule": "exact English source plus unique Russian memory consensus",
        "memory_sources": [str(path) for path in MEMORIES],
        "memory_english": len(candidates),
        "memory_conflicts": len(conflicts),
        "catalogs": counts,
        "restored_rows": len(restored_rows),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
