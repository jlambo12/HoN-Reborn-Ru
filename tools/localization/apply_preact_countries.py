#!/usr/bin/env python3
"""Apply the reviewed standard Russian country display names to Preact."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog" / "preact_ui.jsonl"
MAPPING = ROOT / "translation" / "human" / "preact_countries_ru.json"
REPORT = ROOT / "translation" / "reports" / "preact_countries_ru.json"


def main() -> int:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in CATALOG.read_text(encoding="utf-8-sig").splitlines() if line]
    country_rows = [row for row in rows if row.get("category") == "country_display_name"]
    present = {row["english"] for row in country_rows}
    unknown = sorted(set(mapping) - present)
    applied = 0
    for row in country_rows:
        if row["english"] in mapping:
            row["russian"] = mapping[row["english"]]
            row["translation_origin"] = "HUMAN_STANDARD_COUNTRY_NAME"
            applied += 1
    missing = sorted(row["english"] for row in country_rows if not row.get("russian"))
    errors = []
    if unknown:
        errors.append({"code": "MAPPING_SOURCE_NOT_FOUND", "values": unknown})
    if missing:
        errors.append({"code": "COUNTRY_NAMES_UNTRANSLATED", "values": missing})
    CATALOG.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
    result = {
        "schema_version": 1,
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "country_rows": len(country_rows),
        "manual_mapping_applied": applied,
        "all_have_russian": not missing,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
