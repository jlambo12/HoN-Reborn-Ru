#!/usr/bin/env python3
"""Apply explicitly marked runtime UI batches back to the audit catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog" / "strings.jsonl"
REPORT = ROOT / "translation" / "reports" / "runtime_ui_batches.json"
BUILD_REPORT = ROOT / "reports" / "build.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", action="append", default=[], help="Apply only the named batch file(s)")
    args = parser.parse_args()
    rows = [json.loads(line) for line in CATALOG.read_text(encoding="utf-8-sig").splitlines() if line]
    by_id = {row["id"]: row for row in rows}
    current_upstream_sha = json.loads(BUILD_REPORT.read_text(encoding="utf-8"))["sha256"]
    applied = []
    errors = []
    for path in sorted((ROOT / "translation" / "human").glob("batch_*.json")):
        if args.batch and path.name not in set(args.batch):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not payload.get("catalog_apply"):
            continue
        batch_upstream_sha = payload.get("upstream_sha256")
        count = 0
        for entry in payload.get("entries", []):
            for logical_key in entry.get("keys", []):
                row = by_id.get(logical_key)
                if row is None:
                    errors.append(f"Unknown catalog key: {logical_key}")
                    continue
                if entry.get("english_hash") and entry["english_hash"] != row.get("english_hash"):
                    errors.append(f"CURRENT English hash drift: {logical_key}")
                    continue
                if not entry.get("english_hash") and batch_upstream_sha != current_upstream_sha:
                    errors.append(f"Unpinned batch upstream drift: {logical_key}")
                    continue
                row["russian"] = entry["ru"]
                row["status"] = "TRANSLATE"
                row["runtime_role"] = "DISPLAY_TEXT"
                row["notes"] = f"human runtime batch {payload['batch_id']}"
                row["classification_source"] = "HUMAN_RUNTIME"
                if row.get("english", "").startswith("Enter ") and not entry["ru"].startswith("Enter "):
                    row["protected_terms"] = [term for term in row.get("protected_terms", []) if term != "Enter"]
                    row["locked_spans"] = [span for span in row.get("locked_spans", []) if span.get("canonical_text") != "Enter"]
                for term in entry.get("unlocked_terms", []):
                    row["protected_terms"] = [item for item in row.get("protected_terms", []) if item != term]
                    row["locked_spans"] = [
                        span for span in row.get("locked_spans", [])
                        if span.get("canonical_text") != term
                    ]
                count += 1
        applied.append({"file": path.name, "rows": count})
    result = "PASS" if not errors else "FAIL"
    report = {"schema_version": 1, "result": result, "applied": applied, "errors": errors}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    CATALOG.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
