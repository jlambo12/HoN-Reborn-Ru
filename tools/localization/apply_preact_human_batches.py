#!/usr/bin/env python3
"""Apply stable, manually reviewed Preact translation batches to the audit catalog."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog" / "preact_ui.jsonl"
BATCH_DIR = ROOT / "translation" / "human"
REPORT = ROOT / "translation" / "reports" / "preact_human_batches.json"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    rows = [json.loads(line) for line in CATALOG.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    by_id = {row["id"]: row for row in rows}
    seen: dict[str, Path] = {}
    applied = kept = retired = 0
    batches = []
    errors = []

    for path in sorted(BATCH_DIR.glob("preact_batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        batch_applied = 0
        batch_retired = 0
        for item in payload.get("rows", []):
            row_id = item.get("id")
            if row_id:
                candidates = [by_id[row_id]] if row_id in by_id else []
                expected = 1
            else:
                prefix = item.get("source_prefix", "")
                expected = item.get("expected_matches")
                if not prefix or not isinstance(expected, int) or expected < 1:
                    errors.append(f"phrase row needs source_prefix and expected_matches in {path.name}")
                    continue
                candidates = [row for row in rows if row.get("source_file", "").startswith(prefix) and row.get("english") == item.get("english")]
            if item.get("retired") is True:
                if candidates:
                    label = row_id or f"{item.get('source_prefix')} :: {item.get('english')}"
                    errors.append(f"retired row returned to current catalog: {label} in {path.name}")
                else:
                    retired += 1
                    batch_retired += 1
                continue
            if len(candidates) != expected:
                label = row_id or f"{item.get('source_prefix')} :: {item.get('english')}"
                errors.append(f"expected {expected} current match(es), found {len(candidates)} for {label} in {path.name}")
                continue
            if row_id and candidates[0].get("english") != item.get("english"):
                errors.append(f"source drift for {row_id} in {path.name}")
                continue
            russian = item.get("russian", "")
            if not russian:
                errors.append(f"empty Russian for {row_id} in {path.name}")
                continue
            decision = item.get("decision", "TRANSLATE")
            if decision not in {"TRANSLATE", "KEEP_EN"}:
                errors.append(f"invalid decision {decision} for {row_id}")
                continue
            if decision == "KEEP_EN" and russian != item.get("english"):
                errors.append(f"KEEP_EN differs from source for {row_id or item.get('english')}")
                continue
            duplicate = next((row["id"] for row in candidates if row["id"] in seen), None)
            if duplicate:
                errors.append(f"duplicate id {duplicate}: {seen[duplicate].name}, {path.name}")
                continue
            for row in candidates:
                seen[row["id"]] = path
                row["russian"] = russian
                row["status"] = decision
                row["translation_origin"] = "human_batch"
                row["translation_memory_sources"] = [path.name]
                applied += 1
                kept += decision == "KEEP_EN"
                batch_applied += 1
        batches.append({"file": path.name, "rows": batch_applied, "retired": batch_retired})

    result = "PASS" if not errors else "FAIL"
    report = {"schema_version": 1, "result": result, "applied": applied, "keep_en": kept, "retired": retired, "batches": batches, "errors": errors}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if errors:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    CATALOG.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
